from twisted.internet import defer
from zope.interface import implements, classProvides
from automatron.plugin import IAutomatronPluginFactory
from automatron.client import IAutomatronSignedOnHandler


class AutoJoinPlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronSignedOnHandler)

    name = 'auto_join'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_signed_on(self, client):
        return self._on_signed_on(client)

    @defer.inlineCallbacks
    def _on_signed_on(self, client):
        channels, _ = yield self.controller.config.get_plugin_value(self, client.server, None, 'join')
        if channels is not None:
            for channel in channels.split(','):
                client.join(channel.strip())
