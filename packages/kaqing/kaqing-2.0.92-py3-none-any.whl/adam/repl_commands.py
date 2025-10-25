from adam.commands.alter_tables import AlterTables
from adam.commands.app import App
from adam.commands.app_ping import AppPing
from adam.commands.audit.audit import Audit
from adam.commands.audit.audit_repair_tables import AuditRepairTables
from adam.commands.deploy.code_start import CodeStart
from adam.commands.deploy.code_stop import CodeStop
from adam.commands.deploy.deploy import Deploy
from adam.commands.deploy.deploy_frontend import DeployFrontend
from adam.commands.deploy.deploy_pg_agent import DeployPgAgent
from adam.commands.deploy.deploy_pod import DeployPod
from adam.commands.deploy.undeploy import Undeploy
from adam.commands.deploy.undeploy_frontend import UndeployFrontend
from adam.commands.deploy.undeploy_pg_agent import UndeployPgAgent
from adam.commands.deploy.undeploy_pod import UndeployPod
from adam.commands.describe.describe import Describe
from adam.commands.shell import Shell
from adam.commands.show.show_app_queues import ShowAppQueues
from adam.commands.cp import ClipboardCopy
from adam.commands.bash import Bash
from adam.commands.cd import Cd
from adam.commands.check import Check
from adam.commands.command import Command
from adam.commands.cql.cqlsh import Cqlsh
from adam.commands.devices import DeviceApp, DeviceAuditLog, DeviceCass, DevicePostgres
from adam.commands.exit import Exit
from adam.commands.medusa.medusa import Medusa
from adam.commands.param_get import GetParam
from adam.commands.issues import Issues
from adam.commands.ls import Ls
from adam.commands.nodetool import NodeTool
from adam.commands.postgres.postgres import Postgres
from adam.commands.preview_table import PreviewTable
from adam.commands.pwd import Pwd
from adam.commands.reaper.reaper import Reaper
from adam.commands.repair.repair import Repair
from adam.commands.report import Report
from adam.commands.restart import Restart
from adam.commands.rollout import RollOut
from adam.commands.param_set import SetParam
from adam.commands.show.show import Show
from adam.commands.show.show_app_actions import ShowAppActions
from adam.commands.show.show_app_id import ShowAppId
from adam.commands.show.show_cassandra_status import ShowCassandraStatus
from adam.commands.show.show_cassandra_version import ShowCassandraVersion
from adam.commands.show.show_commands import ShowKubectlCommands
from adam.commands.show.show_host import ShowHost
from adam.commands.show.show_login import ShowLogin
from adam.commands.show.show_params import ShowParams
from adam.commands.show.show_processes import ShowProcesses
from adam.commands.show.show_repairs import ShowRepairs
from adam.commands.show.show_storage import ShowStorage
from adam.commands.show.show_adam import ShowAdam
from adam.commands.watch import Watch

class ReplCommands:
    def repl_cmd_list() -> list[Command]:
        cmds: list[Command] = ReplCommands.navigation() + ReplCommands.cassandra_check() + ReplCommands.cassandra_ops() + \
            ReplCommands.tools() + ReplCommands.app() + ReplCommands.exit()

        intermediate_cmds: list[Command] = [App(), Reaper(), Repair(), Deploy(), Describe(), Show(), Undeploy()]
        ic = [c.command() for c in intermediate_cmds]
        # 1. dedup commands
        deduped = []
        cs = set()
        for cmd in cmds:
            if cmd.command() not in cs and cmd.command() not in ic:
                deduped.append(cmd)
                cs.add(cmd.command())
        # 2. intermediate commands must be added to the end
        deduped.extend(intermediate_cmds)

        # Command.print_chain(Command.chain(cmds))

        return deduped

    def navigation() -> list[Command]:
        return [Ls(), PreviewTable(), DeviceApp(), DevicePostgres(), DeviceCass(), DeviceAuditLog(), Cd(), Pwd(), ClipboardCopy(),
                GetParam(), SetParam(), ShowParams(), ShowKubectlCommands(), ShowLogin(), ShowAdam(), ShowHost()]

    def cassandra_check() -> list[Command]:
        return Describe.cmd_list() + [ShowCassandraStatus(),
                ShowCassandraVersion(), ShowRepairs(), ShowStorage(), ShowProcesses(), Check(), Issues(), NodeTool(), Report()]

    def cassandra_ops() -> list[Command]:
        return [AlterTables()] + Medusa.cmd_list() + [Restart(), RollOut(), Watch()] + Reaper.cmd_list() + Repair.cmd_list()

    def tools() -> list[Command]:
        return [Cqlsh(), Postgres(), Bash(), Shell(), CodeStart(), CodeStop(), DeployFrontend(), UndeployFrontend(),
                DeployPod(), UndeployPod(), DeployPgAgent(), UndeployPgAgent(), AuditRepairTables(), Audit()]

    def app() -> list[Command]:
        return [ShowAppActions(), ShowAppId(), ShowAppQueues(), AppPing(), App()]

    def exit() -> list[Command]:
        return [Exit()]