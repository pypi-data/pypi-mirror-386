import getpass
import os
import re
import time
import traceback
import click
import concurrent
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.key_binding import KeyBindings
import requests

from adam.cli_group import cli
from adam.commands.command import Command
from adam.commands.command_helpers import ClusterCommandHelper
from adam.commands.help import Help
from adam.commands.postgres.postgres_session import PostgresSession
from adam.config import Config
from adam.k8s_utils.kube_context import KubeContext
from adam.k8s_utils.statefulsets import StatefulSets
from adam.log import Log
from adam.repl_commands import ReplCommands
from adam.repl_session import ReplSession
from adam.repl_state import ReplState
from adam.utils import deep_merge_dicts, deep_sort_dict, lines_to_tabular, log2
from adam.apps import Apps
from adam.utils_net import get_my_host
from . import __version__

def enter_repl(state: ReplState):
    if os.getenv('QING_DROPPED', 'false') == 'true':
        log2('You have dropped to bash from another qing instance. Please enter "exit" to go back to qing.')
        return

    cmd_list: list[Command] = ReplCommands.repl_cmd_list() + [Help()]
    # head with the Chain of Responsibility pattern
    cmds: Command = Command.chain(cmd_list)
    session = ReplSession().prompt_session

    def prompt_msg():
        msg = ''
        if state.device == ReplState.P:
            msg = f'{ReplState.P}:'
            pg = PostgresSession(state.namespace, state.pg_path) if state.pg_path else None
            if pg and pg.db:
                msg += pg.db
            elif pg and pg.host:
                msg += pg.host
        elif state.device == ReplState.A:
            msg = f'{ReplState.A}:'
            if state.app_env:
                msg += state.app_env
            if state.app_app:
                msg += f'/{state.app_app}'
        elif state.device == ReplState.L:
            msg = f'{ReplState.L}:'
        else:
            msg = f'{ReplState.C}:'
            if state.pod:
                # cs-d0767a536f-cs-d0767a536f-default-sts-0
                group = re.match(r".*?-.*?-(.*)", state.pod)
                msg += group[1]
            elif state.sts:
                # cs-d0767a536f-cs-d0767a536f-default-sts
                group = re.match(r".*?-.*?-(.*)", state.sts)
                msg += group[1]

        return f"{msg}$ " if state.bash_session else f"{msg}> "

    Log.log2(f'kaqing {__version__}')

    if state.device == ReplState.C:
        ss = StatefulSets.list_sts_name_and_ns()
        if not ss:
            raise Exception("no Cassandra clusters found")
        elif not state.sts and len(ss) == 1 and Config().get('repl.auto-enter-only-cluster', True):
            cluster = ss[0]
            state.sts = cluster[0]
            state.namespace = cluster[1]
            if KubeContext().in_cluster_namespace:
                Config().wait_log(f'Moving to the only Cassandra cluster: {state.sts}...')
            else:
                Config().wait_log(f'Moving to the only Cassandra cluster: {state.sts}@{state.namespace}...')
    elif state.device == ReplState.A:
        if not state.app_env:
            if app := Config().get('repl.auto-enter-app', 'c3/c3'):
                if app != 'no':
                    ea = app.split('/')
                    state.app_env = ea[0]
                    if len(ea) > 1:
                        state.app_app = ea[1]
                        Config().wait_log(f'Moving to {state.app_env}/{state.app_app}...')
                    else:
                        Config().wait_log(f'Moving to {state.app_env}...')

    kb = KeyBindings()

    @kb.add('c-c')
    def _(event):
        event.app.current_buffer.text = ''

    with concurrent.futures.ThreadPoolExecutor(max_workers=Config().get('audit.workers', 3)) as executor:
        # warm up AWS lambda - this log line may timeout and get lost, which is fine
        executor.submit(audit_log, 'entering kaqing repl', state)

        # use sorted command list only for auto-completion
        sorted_cmds = sorted(cmd_list, key=lambda cmd: cmd.command())
        while True:
            try:
                completer = NestedCompleter.from_nested_dict({})
                if not state.bash_session:
                    completions = {}
                    # app commands are available only on a: drive
                    if state.device == ReplState.A and state.app_app:
                        completions = Apps(path='apps.yaml').commands()

                    for cmd in sorted_cmds:
                        s1 = time.time()
                        try:
                            completions = deep_sort_dict(deep_merge_dicts(completions, cmd.completion(state)))
                        finally:
                            if Config().get('debugs.timings', False):
                                log2(f'Timing auto-completion-calc {cmd.command()}: {time.time() - s1:.2f}')

                    # print(json.dumps(completions, indent=4))
                    completer = NestedCompleter.from_nested_dict(completions)

                cmd = session.prompt(prompt_msg(), completer=completer, key_bindings=kb)
                s0 = time.time()

                if state.bash_session:
                    if cmd.strip(' ') == 'exit':
                        state.exit_bash()
                        continue

                    cmd = f'bash {cmd}'

                if cmd and cmd.strip(' ') and not cmds.run(cmd, state):
                    c_sql_tried = False
                    if state.device == ReplState.P:
                        pg = PostgresSession(state.namespace, state.pg_path)
                        if pg.db:
                            c_sql_tried = True
                            cmd = f'pg {cmd}'
                            cmds.run(cmd, state)
                    elif state.device == ReplState.A:
                        if state.app_app:
                            c_sql_tried = True
                            cmd = f'app {cmd}'
                            cmds.run(cmd, state)
                    elif state.device == ReplState.L:
                        c_sql_tried = True
                        cmd = f'audit {cmd}'
                        cmds.run(cmd, state)
                    elif state.sts:
                        c_sql_tried = True
                        cmd = f'cql {cmd}'
                        cmds.run(cmd, state)

                    if not c_sql_tried:
                        log2(f'* Invalid command: {cmd}')
                        log2()
                        lines = [c.help(state) for c in cmd_list if c.help(state)]
                        log2(lines_to_tabular(lines, separator='\t'))
            except EOFError:  # Handle Ctrl+D (EOF) for graceful exit
                break
            except Exception as e:
                if Config().get('debugs.exit-on-error', False):
                    raise e
                else:
                    log2(e)
                    Config().debug(traceback.format_exc())
            finally:
                Config().clear_wait_log_flag()
                if Config().get('debugs.timings', False) and 'cmd' in locals() and 's0' in locals():
                    log2(f'Timing command {cmd}: {time.time() - s0:.2f}')

                # offload audit logging
                if cmd:
                    executor.submit(audit_log, cmd, state)

def audit_log(cmd: str, state: ReplState):
    payload = {
        'cluster': state.namespace if state.namespace else 'NA',
        'ts': time.time(),
        'host': get_my_host(),
        'user': getpass.getuser(),
        'line': cmd.replace('"', '""').replace('\n', ' '),
    }
    audit_endpoint = Config().get("audit.endpoint", "https://4psvtaxlcb.execute-api.us-west-2.amazonaws.com/prod/")
    try:
        response = requests.post(audit_endpoint, json=payload, timeout=Config().get("audit.timeout", 10))
        if response.status_code in [200, 201]:
            Config().debug(response.text)
        else:
            log2(f"Error: {response.status_code} {response.text}")
    except requests.exceptions.Timeout as e:
        log2(f"Timeout occurred: {e}")

@cli.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True), cls=ClusterCommandHelper, help="Enter interactive shell.")
@click.option('--kubeconfig', '-k', required=False, metavar='path', help='path to kubeconfig file')
@click.option('--config', default='params.yaml', metavar='path', help='path to kaqing parameters file')
@click.option('--param', '-v', multiple=True, metavar='<key>=<value>', help='parameter override')
@click.option('--cluster', '-c', required=False, metavar='statefulset', help='Kubernetes statefulset name')
@click.option('--namespace', '-n', required=False, metavar='namespace', help='Kubernetes namespace')
@click.argument('extra_args', nargs=-1, metavar='[cluster]', type=click.UNPROCESSED)
def repl(kubeconfig: str, config: str, param: list[str], cluster:str, namespace: str, extra_args):
    KubeContext.init_config(kubeconfig)
    if not KubeContext.init_params(config, param):
        return

    state = ReplState(device=Config().get('repl.start-drive', 'a'), ns_sts=cluster, namespace=namespace, in_repl=True)
    state, _ = state.apply_device_arg(extra_args)
    enter_repl(state)