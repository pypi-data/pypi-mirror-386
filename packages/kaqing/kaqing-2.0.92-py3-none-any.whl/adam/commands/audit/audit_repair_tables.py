from adam.commands.command import Command
from adam.repl_state import ReplState
from adam.utils_athena import run_audit_query

class AuditRepairTables(Command):
    COMMAND = 'audit repair'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(AuditRepairTables, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return AuditRepairTables.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)

        tables = ['audit']
        if args:
            tables = args

        for table in tables:
            run_audit_query(f'MSCK REPAIR TABLE {table}')

        return state

    def completion(self, state: ReplState):
        if state.device == ReplState.L:
            return super().completion(state)

        return {}

    def help(self, _: ReplState):
        return f"{AuditRepairTables.COMMAND} \t run MSCK REPAIR command for new partition discovery"