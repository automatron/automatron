from twisted.internet import defer
from zope.interface import classProvides, implements
from automatron.command import IAutomatronCommandHandler
from automatron.plugin import IAutomatronPluginFactory, STOP


class AutomatronControlPlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronCommandHandler)

    name = 'control'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    command_map = {
        #command: (help, min_args, max_args, permission)
        'join': ('<channel> [key]', 1, 2, 'channel'),
        'leave': ('<channel> [reason]', 1, 2, 'channel'),
        'say': ('<channel> <message>', 2, 2, 'say'),
        'nickname': ('<nickname>', 1, 1, 'admin'),
    }

    def on_command(self, client, user, command, args):
        if command in self.command_map:
            self._on_command(client, user, command, args)
            return STOP

    @defer.inlineCallbacks
    def _on_command(self, client, user, command, args):
        config = self.command_map[command]

        if config[3] is not None:
            if not (yield self.controller.config.has_permission(client.server, None, user, config[3])):
                client.msg(user, 'You\'re not authorized to do that.')
                return

        if not config[1] <= len(args) <= config[2]:
            client.msg(user, 'Invalid syntax. Use: %s %s' % (command, config[0]))
            return

        getattr(self, '_on_command_%s' % command)(client, user, *args)

    def _on_command_join(self, client, user, channel, key=None):
        if key is not None:
            self.controller.config.update_value('channel', client.server, channel, 'key', key)
            client.join(channel, key)
        else:
            d = self.controller.config.get_value('channel', client.server, channel, 'key')
            d.addCallback(lambda (channel_key, _): client.join(channel, channel_key))

    def _on_command_leave(self, client, user, channel, reason='Leaving...'):
        client.leave(channel, reason)

    def _on_command_say(self, client, user, channel, message):
        client.msg(channel, message)

    def _on_command_nickname(self, client, user, nickname):
        client.setNick(nickname)
