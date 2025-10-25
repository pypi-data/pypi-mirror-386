from adam.commands.command import Command
from adam.k8s_utils.cassandra_nodes import CassandraNodes
from adam.repl_state import ReplState, RequiredState
from adam.utils import log2

class Cat(Command):
    COMMAND = 'cat'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Cat, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return Cat.COMMAND

    def required(self):
        return RequiredState.NAMESPACE

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)
        if not self.validate_state(state):
            return state

        if len(args) < 1:
            if state.in_repl:
                log2('File name is required.')
            else:
                log2('* File name is missing.')
                Command.display_help()

            return 'command-missing'

        arg = args[0]
        if '@' in arg:
            path_and_pod = arg.split('@')
            CassandraNodes.exec(path_and_pod[1], state.namespace, f'cat {path_and_pod[0]}')
        else:
            CassandraNodes.exec(state.pod, state.namespace, f'cat {arg}')

        return state

    def completion(self, state: ReplState):
        return super().completion(state)

    def help(self, _: ReplState):
        return f'{Cat.COMMAND} <path>[@<pod>] \t print content of the file'