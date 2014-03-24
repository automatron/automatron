from twisted.internet import defer, reactor
from zope.interface import implements, classProvides
from automatron.controller.controller import IAutomatronClientActions

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

    def on_signed_on(self, server):
        return self._on_signed_on(server)

    @defer.inlineCallbacks
    def _on_signed_on(self, server):
        channels, _ = yield self.controller.config.get_plugin_value(self, server['server'], None, 'join')
        if channels and channels.strip():
            for channel in channels.split(','):
                self._join_channel(server, channel.strip())

    @defer.inlineCallbacks
    def _join_channel(self, server, channel):
        channel_key = yield self.controller.config.get_value('channel', server['server'], channel, 'key')
        self.controller.plugins.emit(IAutomatronClientActions['join'], server['server'], channel, channel_key)

    def on_channel_joined(self, server, channel):
        self._on_channel_joined(server, channel)

    @defer.inlineCallbacks
    def _on_channel_joined(self, server, channel):
        track, _ = yield self.controller.config.get_plugin_value(self, server['server'], None, 'track')
        if track == 'false':
            return

        channels, channels_rel = yield self.controller.config.get_plugin_value(self, server['server'], None, 'join')
        if channels_rel is None or channels_rel > 0:
            channels = [c.strip() for c in (channels or '').split(',') if c.strip()]
            if not channel in channels:
                channels.append(channel)
                self.controller.config.update_plugin_value(self, server['server'], None, 'join', ','.join(channels))

    def on_channel_left(self, server, channel):
        self._on_channel_left(server, channel)

    @defer.inlineCallbacks
    def _on_channel_left(self, server, channel):
        track, _ = yield self.controller.config.get_plugin_value(self, server['server'], None, 'track')
        if track == 'false':
            return

        channels, channels_rel = yield self.controller.config.get_plugin_value(self, server['server'], None, 'join')
        if channels_rel is not None and channels_rel > 0:
            channels = [c.strip() for c in (channels or '').split(',') if c.strip()]
            if channel in channels:
                channels.remove(channel)
                self.controller.config.update_plugin_value(self, server['server'], None, 'join', ','.join(channels))

    def on_channel_kicked(self, server, channel, kicker, message):
        reactor.callLater(3, self._join_channel, server, channel)
