from twisted.internet import defer
from zope.interface import implements, classProvides

from automatron.backend.plugin import IAutomatronPluginFactory
from automatron.controller.client import IAutomatronChannelJoinedHandler


class JoinMessagePlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronChannelJoinedHandler)

    name = 'join_message'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_channel_joined(self, server, channel):
        return self._on_channel_joined(server, channel)

    @defer.inlineCallbacks
    def _on_channel_joined(self, server, channel):
        message, message_rel = yield self.controller.config.get_plugin_value(self, server['server'], channel, 'message')
        action, action_rel = yield self.controller.config.get_plugin_value(self, server['server'], channel, 'action')

        if message is not None and (action is None or message_rel > action_rel):
            f = self.controller.message
        elif action is not None:
            f = self.controller.action
            message = action
        else:
            return

        f(server['server'], channel, message % server)
