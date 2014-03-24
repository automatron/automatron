from automatron.controller.plugin import IAutomatronEventHandler


class IAutomatronCommandHandler(IAutomatronEventHandler):
    def on_command(client, user, command, args):
        """
        Called when a user issues a command.
        """
