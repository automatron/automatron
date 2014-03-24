from automatron.core.event import IAutomatronEventHandler


class IAutomatronCommandHandler(IAutomatronEventHandler):
    def on_command(server, user, command, args):
        """
        Called when a user issues a command.
        """
