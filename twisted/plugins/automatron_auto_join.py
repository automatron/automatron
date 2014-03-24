from twisted.internet import defer, reactor
from zope.interface import implements, classProvides

from automatron.controller.plugin import IAutomatronPluginFactory
from automatron.controller.client import IAutomatronSignedOnHandler, IAutomatronChannelJoinedHandler,\
    IAutomatronChannelLeftHandler, IAutomatronChannelKickedHandler


class AutoJoinPlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(
        IAutomatronSignedOnHandler,
        IAutomatronChannelJoinedHandler,
        IAutomatronChannelLeftHandler,
        IAutomatronChannelKickedHandler,
    )

    name = 'auto_join'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_signed_on(self, client):
        return self._on_signed_on(client)

    @defer.inlineCallbacks
    def _on_signed_on(self, client):
        channels, _ = yield self.controller.config.get_plugin_value(self, client.server, None, 'join')
        if channels and channels.strip():
            for channel in channels.split(','):
                channel = channel.strip()
                d = self.controller.config.get_value('channel', client.server, channel, 'key')
                d.addCallback(lambda (channel_key, _), c=channel: client.join(c, channel_key))

    def on_channel_joined(self, client, channel):
        self._on_channel_joined(client, channel)

    @defer.inlineCallbacks
    def _on_channel_joined(self, client, channel):
        track, _ = yield self.controller.config.get_plugin_value(self, client.server, None, 'track')
        if track == 'false':
            return

        channels, channels_rel = yield self.controller.config.get_plugin_value(self, client.server, None, 'join')
        if channels_rel is None or channels_rel > 0:
            channels = [c.strip() for c in (channels or '').split(',') if c.strip()]
            if not channel in channels:
                channels.append(channel)
                self.controller.config.update_plugin_value(self, client.server, None, 'join', ','.join(channels))

    def on_channel_left(self, client, channel):
        self._on_channel_left(client, channel)

    @defer.inlineCallbacks
    def _on_channel_left(self, client, channel):
        track, _ = yield self.controller.config.get_plugin_value(self, client.server, None, 'track')
        if track == 'false':
            return

        channels, channels_rel = yield self.controller.config.get_plugin_value(self, client.server, None, 'join')
        if channels_rel is not None and channels_rel > 0:
            channels = [c.strip() for c in (channels or '').split(',') if c.strip()]
            if channel in channels:
                channels.remove(channel)
                self.controller.config.update_plugin_value(self, client.server, None, 'join', ','.join(channels))

    def on_channel_kicked(self, client, channel, kicker, message):
        reactor.callLater(3, client.join, channel)
