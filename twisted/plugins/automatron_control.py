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
        'identify': ('[channel]', 0, 1, None)
    }

    def on_command(self, client, user, command, args):
        if command in self.command_map:
            self._on_command(client, user, command, args)
            return STOP

    @defer.inlineCallbacks
    def _on_command(self, client, user, command, args):
        nickname = client.parse_user(user)[0]
        config = self.command_map[command]

        if config[3] is not None:
            if not (yield self.controller.config.has_permission(client.server, None, user, config[3])):
                client.msg(nickname, 'You\'re not authorized to do that.')
                return

        if not config[1] <= len(args) <= config[2]:
            client.msg(nickname, 'Invalid syntax. Use: %s %s' % (command, config[0]))
            return

        getattr(self, '_on_command_%s' % command)(client, user, *args)

    def _on_command_join(self, client, user, channel, key=None):
        if key is not None:
            self.controller.config.update_value('channel', client.server, channel, 'key', key)
            client.join(channel, key)
        else:
            d = self.controller.config.get_value('channel', client.server, channel, 'key')
            d.addCallback(lambda channel_key, _: client.join(channel, channel_key))

    def _on_command_leave(self, client, user, channel, reason=None):
        client.leave(channel, reason if reason is not None else 'Leaving...')

    def _on_command_say(self, client, user, channel, message):
        client.msg(channel, message)

    @defer.inlineCallbacks
    def _on_command_identify(self, client, user, channel=None):
        nickname = client.parse_user(user)[0]
        username, username_relevance = yield self.controller.config.get_username_by_hostmask(client.server, user)
        if username is not None:
            if username_relevance == 0:
                identity = 'You are globally known as %s' % username
            else:
                identity = 'You are known as %s' % username

            role, role_relevance = yield self.controller.config.get_role_by_username(client.server, channel, username)
            if role_relevance is not None and role_relevance < username_relevance:
                role = role_relevance = None

            if role_relevance is None:
                client.msg(nickname, identity)
            elif role_relevance in (2, 3):
                client.msg(nickname, '%s and your role in %s is %s' % (identity, channel, role))
            else:
                client.msg(nickname, '%s and your role is %s' % (identity, role))
        else:
            client.msg(nickname, 'I don\'t know you...')
