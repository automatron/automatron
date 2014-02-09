import random
import re
from twisted.internet import protocol, reactor
from twisted.words.protocols import irc
from twisted.python import log
from automatron.plugin import IAutomatronEventHandler

i = random.randrange(10000)
DEFAULT_NICKNAME = 'automatron%d,automatron%d_,automatron%d__' % (i, i, i)
DEFAULT_REALNAME = 'Automatron %d' % i
USER_RE = re.compile(r'(.*)?!(.*)?@(.*)')


class Client(irc.IRCClient):
    def __init__(self, controller, server, config):
        self.controller = controller
        self.server = server
        self.config = config
        self.nicknames = [
            n.strip()
            for n in self.config.get('nickname', DEFAULT_NICKNAME).split(',')
        ]
        self.nickname = self.nicknames[0]
        self.realname = self.config.get('realname', DEFAULT_REALNAME)

    def logPrefix(self):
        return '%s' % self.server

    def emit(self, event, *args):
        self.controller.plugins.emit(event, self, *args)

    def parse_user(self, user):
        m = USER_RE.match(user)
        if not m:
            return user, None, None
        else:
            return m.groups()

    def alterCollidedNick(self, nickname):
        new_nick = self.nicknames[(self.nicknames.index(nickname) + 1) % len(self.nicknames)]
        log.msg('Nickname %s is taken, trying %s.' % (nickname, new_nick))
        return new_nick

    def connectionMade(self):
        log.msg('Connected')
        irc.IRCClient.connectionMade(self)
        self.emit('connection_made')

    def connectionLost(self, reason):
        log.msg('Connection lost')
        irc.IRCClient.connectionLost(self, reason)
        self.emit('connection_lost', reason)

    def receivedMOTD(self, motd):
        log.msg('MOTD:\n%s' % '\n'.join(motd))
        self.emit('server_motd', motd)

    def created(self, when):
        log.msg('Created: %s' % when)
        self.emit('server_created', when)

    def yourHost(self, info):
        log.msg('Host: %s' % info)
        self.emit('server_host', info)

    def myInfo(self, servername, version, umodes, cmodes):
        log.msg('Servername: %s, Version: %s, umodes: %s, cmodes: %s' % (
            servername,
            version,
            umodes,
            cmodes
        ))
        self.emit('server_info', servername, version, umodes, cmodes)

    def isupport(self, options):
        log.msg('Supports: %s' % options)
        self.emit('server_support', options)

    def luserClient(self, info):
        log.msg('Clients: %s' % info)
        self.emit('luser_client', info)

    def luserChannels(self, channels):
        log.msg('Channels: %s' % channels)
        self.emit('luser_channels', channels)

    def luserOp(self, ops):
        log.msg('Operators: %s' % ops)
        self.emit('luser_op', ops)

    def luserMe(self, info):
        log.msg('About server: %s' % info)
        self.emit('luser_me', info)

    def signedOn(self):
        log.msg('Signed on')
        self.emit('signed_on')

    def nickChanged(self, nick):
        log.msg('Nickname changed from %s to %s' % (self.nickname, nick))
        self.emit('nick_changed', nick)

    def modeChanged(self, user, channel, set, modes, args):
        log.msg('[%s] *** Mode %s%s on %s by %s' % (
            channel,
            set and '+' or '-',
            modes,
            args,
            user,
        ))
        self.emit('mode_changed', user, channel, set, modes, args)

    def joined(self, channel):
        log.msg('Joined channel %s' % channel)
        self.emit('channel_joined', channel)

    def left(self, channel):
        log.msg('Left channel %s' % channel)
        self.emit('channel_left', channel)

    def topicUpdated(self, user, channel, newTopic):
        log.msg('[%s] *** topic changed by %s: %s' % (
            channel,
            self.parse_user(user)[0],
            newTopic
        ))
        self.emit('channel_topic_changed', user, channel, newTopic)

    def kickedFrom(self, channel, kicker, message):
        log.msg('Kicked from %s by %s (reason: %s)' % (channel, kicker, message))
        self.emit('kicked', channel, kicker, message)

    def privmsg(self, user, channel, message):
        log.msg('[%s] %s: %s' % (channel, self.parse_user(user)[0], message))
        self.emit('message', user, channel, message)

    def noticed(self, user, channel, message):
        log.msg('|%s| %s: %s' % (channel, self.parse_user(user)[0], message))
        self.emit('notice', user, channel, message)

    def action(self, user, channel, data):
        log.msg('[%s] *%s %s' % (channel, self.parse_user(user)[0], data))
        self.emit('action', user, channel, data)

    def userJoined(self, user, channel):
        log.msg('[%s] *** user %s joined' % (channel, self.parse_user(user)[0]))
        self.emit('user_joined', user, channel)

    def userLeft(self, user, channel):
        log.msg('[%s] *** user %s left' % (channel, self.parse_user(user)))
        self.emit('user_left', user, channel)

    def userQuit(self, user, quitMessage):
        log.msg('*** user %s quit (reason: %s)' % (self.parse_user(user), quitMessage))
        self.emit('user_quit', user, quitMessage)

    def userKicked(self, kickee, channel, kicker, message):
        log.msg('[%s] user %s was kicked by %s (reason: %s)' % (
            channel,
            self.parse_user(kickee)[0],
            self.parse_user(kicker)[0],
            message
        ))
        self.emit('user_kicked', kickee, channel, kicker, message)

    def userRenamed(self, oldname, newname):
        log.msg('*** %s is now known as %s' % (oldname, newname))
        self.emit('user_nickname_changed', oldname, newname)

    def pong(self, user, secs):
        log.msg('PONG %s %ds' % (user, secs))
        self.emit('pong', user, secs)


class ClientFactory(protocol.ClientFactory):
    def logPrefix(self):
        return self.server

    def __init__(self, controller, server, config):
        self.controller = controller
        self.server = server
        self.config = config

    def buildProtocol(self, addr):
        log.msg('Setting up connection to %s' % addr)
        return Client(self.controller, self.server, self.config)

    def clientConnectionLost(self, connector, reason):
        log.msg('Connection lost (%s), reconnecting' % reason)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        log.msg('Connection failed (%s), reconnecting in 10s' % reason)
        reactor.callLater(10000, connector.connect)


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
