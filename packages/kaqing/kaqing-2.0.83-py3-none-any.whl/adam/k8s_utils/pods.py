from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import time
from typing import TypeVar, cast
from kubernetes import client
from kubernetes.stream import stream
from kubernetes.stream.ws_client import ERROR_CHANNEL

from adam.config import Config
from adam.k8s_utils.volumes import ConfigMapMount
from adam.pod_exec_result import PodExecResult
from adam.utils import elapsed_time, log2
from .kube_context import KubeContext

T = TypeVar('T')
_TEST_POD_EXEC_OUTS: PodExecResult = None

# utility collection on pods; methods are all static
class Pods:
    def set_test_pod_exec_outs(outs: PodExecResult):
        global _TEST_POD_EXEC_OUTS
        _TEST_POD_EXEC_OUTS = outs

        return _TEST_POD_EXEC_OUTS

    def delete(pod_name: str, namespace: str, grace_period_seconds: int = None):
        try:
            v1 = client.CoreV1Api()
            api_response = v1.delete_namespaced_pod(pod_name, namespace, grace_period_seconds=grace_period_seconds)
        except Exception as e:
            log2("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

    def delete_with_selector(namespace: str, label_selector: str, grace_period_seconds: int = None):
        v1 = client.CoreV1Api()

        ret = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        for i in ret.items:
            v1.delete_namespaced_pod(name=i.metadata.name, namespace=namespace, grace_period_seconds=grace_period_seconds)

    def on_pods(pods: list[str],
                namespace: str,
                body: Callable[[ThreadPoolExecutor, str, str, bool], T],
                post: Callable[[T], T] = None,
                action: str = 'action', max_workers=0, show_out=True, on_any = False) -> list[T]:
        show_out = KubeContext.show_out(show_out)

        if not max_workers:
            max_workers = Config().action_workers(action, 0)
        if not on_any and max_workers > 0:
            # if parallel, node sampling is suppressed
            if KubeContext.show_parallelism():
                log2(f'Executing on all nodes from statefulset in parallel...')
            start_time = time.time()
            try:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # disable stdout from the pod_exec, then show the output in a for loop
                    futures = [body(executor, pod, namespace, show_out) for pod in pods]
                    if len(futures) == 0:
                        return cast(list[T], [])

                rs = [future.result() for future in as_completed(futures)]
                if post:
                    rs = [post(r, show_out=show_out) for r in rs]

                return rs
            finally:
                if KubeContext.show_parallelism():
                    log2(f"Parallel {action} elapsed time: {elapsed_time(start_time)} with {max_workers} workers")
        else:
            results: list[T] = []

            samples = 1 if on_any else Config().action_node_samples(action, sys.maxsize)
            l = min(len(pods), samples)
            adj = 'all'
            if l < len(pods):
                adj = f'{l} sample'
            if show_out:
                log2(f'Executing on {adj} nodes from statefulset...')
            for pod_name in pods:
                try:
                    # disable stdout from the pod_exec, then show the output in a for loop
                    result = body(None, pod_name, namespace, False)
                    if post:
                        result = post(result, show_out=show_out)
                    results.append(result)
                    if result:
                        l -= 1
                        if not l:
                            break
                except Exception as e:
                    log2(e)

            return results

    def exec(pod_name: str, container: str, namespace: str, command: str, show_out = True, throw_err = False, interaction: Callable[[any, list[str]], any] = None):
        if _TEST_POD_EXEC_OUTS:
            return _TEST_POD_EXEC_OUTS

        show_out = KubeContext.show_out(show_out)

        api = client.CoreV1Api()

        exec_command = ["/bin/sh", "-c", command]
        k_command = f'kubectl exec {pod_name} -c {container} -n {namespace} -- {command}'
        if show_out:
            print(k_command)

        resp = stream(
            api.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=exec_command,
            container=container,
            stderr=True,
            stdin=True,
            stdout=True,
            tty=True,
            _preload_content=False,
        )

        stdout = []
        stderr = []
        error_output = None
        try:
            while resp.is_open():
                resp.update(timeout=1)
                if resp.peek_stdout():
                    frag = resp.read_stdout()
                    stdout.append(frag)
                    if show_out: print(frag, end="")

                    if interaction:
                        interaction(resp, stdout)
                if resp.peek_stderr():
                    frag = resp.read_stderr()
                    stderr.append(frag)
                    if show_out: print(frag, end="")

            try:
                # get the exit code from server
                error_output = resp.read_channel(ERROR_CHANNEL)
            except Exception:
                pass
        except Exception as e:
            if throw_err:
                raise e
            else:
                log2(e)
        finally:
            resp.close()

        return PodExecResult("".join(stdout), "".join(stderr), k_command, error_output)

    def get_container(namespace: str, pod_name: str, container_name: str):
        pod = Pods.get(namespace, pod_name)
        if not pod:
            return None

        for container in pod.spec.containers:
            if container_name == container.name:
                return container

        return None

    def get(namespace: str, pod_name: str):
        v1 = client.CoreV1Api()
        return v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    def get_with_selector(namespace: str, label_selector: str):
        v1 = client.CoreV1Api()

        ret = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        for i in ret.items:
            return v1.read_namespaced_pod(name=i.metadata.name, namespace=namespace)

    def create_pod_spec(name: str, image: str, image_pull_secret: str,
                        envs: list, container_security_context: client.V1SecurityContext,
                        volume_name: str, pvc_name:str, mount_path:str,
                        command: list[str]=None, sa_name : str = None, config_map_mount: ConfigMapMount = None,
                        restart_policy="Never"):
        volume_mounts = []
        if volume_name and pvc_name and mount_path:
            volume_mounts=[client.V1VolumeMount(mount_path=mount_path, name=volume_name)]

        if config_map_mount:
            volume_mounts.append(client.V1VolumeMount(mount_path=config_map_mount.mount_path, sub_path=config_map_mount.sub_path, name=config_map_mount.name()))

        container = client.V1Container(name=name, image=image, env=envs, security_context=container_security_context, command=command,
                                    volume_mounts=volume_mounts)

        volumes = []
        if volume_name and pvc_name and mount_path:
            volumes=[client.V1Volume(name=volume_name, persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name))]

        security_context = None
        if not sa_name:
            security_context=client.V1PodSecurityContext(run_as_user=1001, run_as_group=1001, fs_group=1001)

        if config_map_mount:
            volumes.append(client.V1Volume(name=config_map_mount.name(), config_map=client.V1ConfigMapVolumeSource(name=config_map_mount.config_map_name)))

        return client.V1PodSpec(
            restart_policy=restart_policy,
            containers=[container],
            image_pull_secrets=[client.V1LocalObjectReference(name=image_pull_secret)],
            security_context=security_context,
            service_account_name=sa_name,
            volumes=volumes
        )

    def create(namespace: str, pod_name: str, image: str,
               command: list[str] = None,
               secret: str = None,
               env: dict[str, any] = {},
               container_security_context: client.V1SecurityContext = None,
               labels: dict[str, str] = {},
               volume_name: str = None,
               pvc_name: str = None,
               mount_path: str = None,
               sa_name: str = None,
               config_map_mount: ConfigMapMount = None):
        v1 = client.CoreV1Api()
        envs = []
        for k, v in env.items():
            envs.append(client.V1EnvVar(name=str(k), value=str(v)))
        pod = Pods.create_pod_spec(pod_name, image, secret, envs, container_security_context, volume_name, pvc_name, mount_path, command=command,
                                   sa_name=sa_name, config_map_mount=config_map_mount)
        return v1.create_namespaced_pod(
            namespace=namespace,
            body=client.V1Pod(spec=pod, metadata=client.V1ObjectMeta(
                name=pod_name,
                labels=labels
            ))
        )

    def wait_for_running(namespace: str, pod_name: str, msg: str = None, label_selector: str = None):
        cnt = 2
        while (cnt < 302 and Pods.get_with_selector(namespace, label_selector) if label_selector else Pods.get(namespace, pod_name)).status.phase != 'Running':
            if not msg:
                msg = f'Waiting for the {pod_name} pod to start up.'

            max_len = len(msg) + 3
            mod = cnt % 3
            padded = ''
            if mod == 0:
                padded = f'\r{msg}'.ljust(max_len)
            elif mod == 1:
                padded = f'\r{msg}.'.ljust(max_len)
            else:
                padded = f'\r{msg}..'.ljust(max_len)
            log2(padded, nl=False)
            cnt += 1
            time.sleep(1)

        log2(f'\r{msg}..'.ljust(max_len), nl=False)
        if cnt < 302:
            log2(' OK')
        else:
            log2(' Timed Out')

    def completed(namespace: str, pod_name: str):
        return Pods.get(namespace, pod_name).status.phase in ['Succeeded', 'Failed']