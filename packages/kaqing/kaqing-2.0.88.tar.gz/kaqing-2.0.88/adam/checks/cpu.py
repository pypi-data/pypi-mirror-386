from kubernetes.utils import parse_quantity

from adam.checks.check import Check
from adam.checks.check_context import CheckContext
from adam.checks.check_result import CheckResult
from adam.checks.issue import Issue
from adam.config import Config
from adam.k8s_utils.cassandra_nodes import CassandraNodes
from adam.k8s_utils.custom_resources import CustomResources

class Cpu(Check):
    def name(self):
        return 'cpu'

    def check(self, ctx: CheckContext) -> CheckResult:
        issues: list[Issue] = []

        details = {
            'name': ctx.pod,
            'namespace': ctx.namespace,
            'statefulset': ctx.statefulset,
            'cpu': 'Unknown',
            'idle': 'Unknown'
        }

        try:
            idle = 'Unknown'
            result = CassandraNodes.exec(ctx.pod, ctx.namespace, "mpstat 5 2 | grep Average | awk '{print $NF}'", show_out=ctx.show_output)
            lines = result.stdout.strip(' \r\n').split('\n')
            line = lines[len(lines) - 1].strip(' \r')
            idle = details['idle'] = line

            busy_threshold = Config().get('checks.cpu-busy-threshold', 98.0)
            if  busy_threshold != 0.0 and idle != "Unknown" and (100 - float(idle)) > busy_threshold:
                issues.append(Issue(
                    statefulset=ctx.statefulset,
                    namespace=ctx.namespace,
                    pod=ctx.pod,
                    category='cpu',
                    desc=f'CPU is too busy: busy={round(100 - float(idle), 2)}%',
                    suggestion=f"qing restart {ctx.pod}@{ctx.namespace}"
                ))

            container = CustomResources.get_metrics(ctx.namespace, ctx.pod, container_name='cassandra')

            usage = 'Unknown'
            if container:
                usage = details['cpu'] = container["usage"]["cpu"]

            cpu_threshold = Config().get('checks.cpu-threshold', 0.0)
            if  cpu_threshold != 0.0 and usage != "Unknown" and parse_quantity(usage) > cpu_threshold:
                issues.append(Issue(
                    statefulset=ctx.statefulset,
                    namespace=ctx.namespace,
                    pod=ctx.pod,
                    category='cpu',
                    desc=f'CPU is too busy: {usage}',
                    suggestion=f"qing restart {ctx.pod}@{ctx.namespace}"
                ))
        except Exception as e:
            issues.append(self.issue_from_err(sts_name=ctx.statefulset, ns=ctx.namespace, pod_name=ctx.pod, exception=e))

        return CheckResult(self.name(), details, issues)

    def help(self):
        return f'{Cpu().name()}: check cpu busy percentage with mpstats'