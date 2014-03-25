from twisted.internet import defer
from zope.interface import classProvides, implements

from automatron.backend.command import IAutomatronCommandHandler
from automatron.backend.plugin import IAutomatronPluginFactory
from automatron.core.event import STOP


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

    def on_command(self, server, user, command, args):
        if command in self.command_map:
            self._on_command(server, user, command, args)
            return STOP

    @defer.inlineCallbacks
    def _on_command(self, server, user, command, args):
        config = self.command_map[command]

        if config[3] is not None:
            if not (yield self.controller.config.has_permission(server['server'], None, user, config[3])):
                self.controller.message(server['server'], user, 'You\'re not authorized to do that.')
                return

        if not config[1] <= len(args) <= config[2]:
            self.controller.message(server['server'], user, 'Invalid syntax. Use: %s %s' % (command, config[0]))
            return

        getattr(self, '_on_command_%s' % command)(server, user, *args)

    @defer.inlineCallbacks
    def _on_command_join(self, server, user, channel, key=None):
        if key is not None:
            self.controller.config.update_value('channel', server['server'], channel, 'key', key)
        else:
            key = yield self.controller.config.get_value('channel', server['server'], channel, 'key')

        self.controller.join(server['server'], channel, key)

    def _on_command_leave(self, server, user, channel, reason='Leaving...'):
        self.controller.leave(server['server'], channel, reason)

    def _on_command_say(self, server, user, channel, message):
        self.controller.message(server['server'], channel, message)

    def _on_command_nickname(self, server, user, nickname):
        self.controller.nick(server['server'], nickname)
