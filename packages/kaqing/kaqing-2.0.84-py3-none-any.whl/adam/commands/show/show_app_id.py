from adam.commands.command import Command
from adam.k8s_utils.custom_resources import CustomResources
from adam.repl_state import ReplState, RequiredState
from adam.utils import log

class ShowAppId(Command):
    COMMAND = 'show app id'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(ShowAppId, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return ShowAppId.COMMAND

    def required(self):
        return RequiredState.CLUSTER_OR_POD

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, _ = state.apply_args(args)
        if not self.validate_state(state):
            return state

        c3_app_id = 'Unknown'

        apps = CustomResources.get_app_ids()
        cr_name = CustomResources.get_cr_name(state.sts if state.sts else state.pod, namespace=state.namespace)
        if cr_name in apps:
            c3_app_id = (apps[cr_name])

        log(c3_app_id)

        return c3_app_id

    def completion(self, state: ReplState):
        return super().completion(state)

    def help(self, _: ReplState):
        return f'{ShowAppId.COMMAND}\t show app id for the Cassandra cluster'