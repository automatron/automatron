from twisted.internet import defer
from zope.interface import implements, classProvides

from automatron.controller.plugin import IAutomatronPluginFactory
from automatron.controller.client import IAutomatronChannelJoinedHandler


class JoinMessagePlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronChannelJoinedHandler)

    name = 'join_message'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_channel_joined(self, client, channel):
        return self._on_channel_joined(client, channel)

    @defer.inlineCallbacks
    def _on_channel_joined(self, client, channel):
        message, message_rel = yield self.controller.config.get_plugin_value(self, client.server, channel, 'message')
        action, action_rel = yield self.controller.config.get_plugin_value(self, client.server, channel, 'action')

        if message is not None and (action is None or message_rel > action_rel):
            f = client.msg
        elif action is not None:
            f = client.describe
            message = action
        else:
            return

        f(channel, message % {
            'nickname': client.nickname,
            'realname': client.realname,
        })
