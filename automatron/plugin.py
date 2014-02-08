import sys
from twisted.plugin import getPlugins, IPlugin
from twisted.python import log
import zope.interface
import zope.interface.verify


class IAutomatronPluginFactory(IPlugin):
    name = zope.interface.Attribute("""The name of this plugin.""")
    priority = zope.interface.Attribute("""The priority with which the plugin will be executed.""")

    def __call__(controller):
        """
        Create a new controller.
        """


class IAutomatronEventHandler(zope.interface.Interface):
    """
    Abstract interface which is the base of all event handler interfaces.
    """


class IAutomatronConnectionMadeHandler(IAutomatronEventHandler):
    def on_connection_made(client):
        """
        Called when a connection to the server is made.
        """


class IAutomatronConnectionLostHandler(IAutomatronEventHandler):
    def on_connection_lost(client, reason):
        """
        Called when the connection to the server is lost.
        """


class IAutomatronServerMotdHandler(IAutomatronEventHandler):
    def on_server_motd(client, motd):
        """
        Called when the message of the day is received from the server
        """


class IAutomatronServerCreatedHandler(IAutomatronEventHandler):
    def on_server_created(client, when):
        """
        Called when the server tells us when it was first created.
        """


class IAutomatronServerHostHandler(IAutomatronEventHandler):
    def on_server_host(client, info):
        """
        Called when the server tells us what its hostname is.
        """


class IAutomatronServerInfoHandler(IAutomatronEventHandler):
    def on_server_info(client, info):
        """
        Called when the server tells us its basic information
        """


class IAutomatronServerSupportHandler(IAutomatronEventHandler):
    def on_server_support(client, info):
        """
        Called when the server describes its capabilities.
        """


class IAutomatronLuserClientHandler(IAutomatronEventHandler):
    def on_luser_client(client, info):
        """
        Called when the server tells us how many clients are connected.
        """


class IAutomatronLuserChannelsHandler(IAutomatronEventHandler):
    def on_luser_channels(client, channels):
        """
        Called when the server tells us how many channels it serves.
        """


class IAutomatronLuserOpHandler(IAutomatronEventHandler):
    def on_luser_op(client, ops):
        """
        Called when the server tells us how many operators there are.
        """


class IAutomatronLuserMeHandler(IAutomatronEventHandler):
    def on_luser_me(client, info):
        """
        Called when the server tells us about this particular node on the network.
        """


class IAutomatronSignedOnHandler(IAutomatronEventHandler):
    def on_signed_on(client):
        """
        Called when the session with the IRC server is established.
        """


class IAutomatronNicknameChangedHandler(IAutomatronEventHandler):
    def on_nickname_changed(client, nick):
        """
        Called when our nickname has changed.
        """


class IAutomatronModeChangedHandler(IAutomatronEventHandler):
    def on_mode_changed(client, user, channel, set, modes, args):
        """
        Called when we're notified of one or more mode changes on a channel or user.
        """


class IAutomatronChannelJoinedHandler(IAutomatronEventHandler):
    def on_channel_joined(client, channel):
        """
        Called when we've joined a channel.
        """


class IAutomatronChannelLeftHandler(IAutomatronEventHandler):
    def on_channel_left(client, channel):
        """
        Called when we've left a channel.
        """


class IAutomatronChannelKickedHandler(IAutomatronEventHandler):
    def on_channel_kicked(client, channel, kicker, message):
        """
        Called when we've been kicked from a channel.
        """


class IAutomatronChannelTopicChangedHandler(IAutomatronEventHandler):
    def on_channel_topic_changed(client, topic):
        """
        Called when the topic of a room we're in changes.
        """


class IAutomatronMessageHandler(IAutomatronEventHandler):
    def on_message(client, user, channel, message):
        """
        Called when we receive a message.
        """


class IAutomatronNoticeHandler(IAutomatronEventHandler):
    def on_notice(client, user, channel, message):
        """
        Called when we receive a notice.
        """


class IAutomatronActionHandler(IAutomatronEventHandler):
    def on_action(client):
        """
        Called when a user performs an action.
        """


class IAutomatronUserJoinedHandler(IAutomatronEventHandler):
    def on_user_joined(client, user, channel):
        """
        Called when a user joins a channel we're in.
        """


class IAutomatronUserLeftHandler(IAutomatronEventHandler):
    def on_user_left(client, user, channel):
        """
        Called when a user leaves a channel we're in.
        """


class IAutomatronUserQuitHandler(IAutomatronEventHandler):
    def on_user_quit(client, user, message):
        """
        Called when a user we share a room with quits.
        """


class IAutomatronUserKickedHandler(IAutomatronEventHandler):
    def on_user_kicked(client, kickee, channel, kicker, message):
        """
        Called when a user is kicked from a room we're in.
        """


class IAutomatronUserNicknameChangedHandler(IAutomatronEventHandler):
    def on_user_nickname_changed(client, old_name, new_name):
        """
        Called when the nickname of a user changed.
        """


class IAutomatronPongHandler(IAutomatronEventHandler):
    def on_pong(client, user, secs):
        """
        Called when we received a CTCP PONG reply.
        """


STOP = object()


class PluginManager(object):
    def __init__(self, controller):
        self.controller = controller
        self.plugins = []
        self.reload()

    def reload(self):
        plugins = []
        plugin_classes = list(getPlugins(IAutomatronPluginFactory))
        for plugin_class in plugin_classes:
            try:
                zope.interface.verify.verifyObject(IAutomatronPluginFactory, plugin_class)
            except (zope.interface.verify.BrokenImplementation, zope.interface.verify.BrokenMethodImplementation) as e:
                print >>sys.stderr, 'Invalid plugin: %s' % plugin_class.__name__
                print >>sys.stderr, e
                continue
            for iface in zope.interface.implementedBy(plugin_class):
                if iface.extends(IAutomatronEventHandler):
                    try:
                        zope.interface.verify.verifyClass(iface, plugin_class)
                    except zope.interface.verify.BrokenMethodImplementation as e:
                        print >>sys.stderr, 'Invalid plugin: %s' % plugin_class
                        print >>sys.stderr, e
                        break
            else:
                plugins.append(plugin_class(self.controller))
        self.plugins = sorted(plugins, key=lambda i: i.priority)

    def emit(self, event, *args):
        method = 'on_%s' % event
        for plugin in self.plugins:
            for iface in zope.interface.providedBy(plugin):
                if iface.extends(IAutomatronEventHandler) and method in iface:
                    f = getattr(plugin, method)
                    if f(*args) is STOP:
                        break
