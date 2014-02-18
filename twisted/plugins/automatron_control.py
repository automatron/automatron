from twisted.internet import defer
from zope.interface import classProvides, implements
from automatron.command import IAutomatronCommandHandler
from automatron.plugin import IAutomatronPluginFactory, STOP


class AutomatronControlPlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronCommandHandler)

    name = 'notify_control'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    command_map = {
        #command: (help, min_args, max_args, permission)
        'join': ('<channel> [key]', 1, 2, 'channel'),
        'leave': ('<channel> [reason]', 1, 2, 'channel'),
        'say': ('<channel> <message>', 2, 2, 'say'),
    }

    def on_command(self, client, user, command, args):
        if command in self.command_map:
            self._on_command(client, user, command, args)
            return STOP

    @defer.inlineCallbacks
    def _on_command(self, client, user, command, args):
        nickname = client.parse_user(user)[0]
        config = self.command_map[command]

        if not (yield self.controller.config.has_permission(client.server, None, user, config[3])):
            client.msg(nickname, 'You\'re not authorized to do that.')
            return

        if not config[1] <= len(args) <= config[2]:
            client.msg(nickname, 'Invalid syntax. Use: %s %s' % (command, config[0]))
            return

        getattr(self, '_on_command_%s' % command)(client, user, *args)

    def _on_command_join(self, client, user, channel, key=None):
        client.join(channel, key)

    def _on_command_leave(self, client, user, channel, reason=None):
        client.leave(channel, reason if reason is not None else 'Leaving...')

    def _on_command_say(self, client, user, channel, message):
        client.msg(channel, message)
