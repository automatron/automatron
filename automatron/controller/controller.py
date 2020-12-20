from twisted.application import internet
from twisted.internet import defer, ssl
from twisted.python import log
from zope.interface import implements
from automatron.controller.client import ClientFactory
from automatron.controller.router import Router
from automatron.core.controller import BaseController
from automatron.core.event import IAutomatronEventHandler, EventManager


DEFAULT_PORT = 6667


class IAutomatronClientActions(IAutomatronEventHandler):
    def message(server_name, user, message):
        """
        Send a message to user on a server we're connected to.
        """

    def action(server_name, user, message):
        """
        Perform an action (/me ..).
        """

    def join(server_name, channel, key=None):
        """
        Join a channel on a server.
        """

    def leave(server_name, channel, reason=None):
        """
        Leave a channel on a server.
        """

    def nick(server_name, nickname):
        """
        Change nickname.
        """


class Controller(BaseController):
    implements(IAutomatronClientActions)
    priority = 100
    name = 'controller'

    def __init__(self, config_file):
        BaseController.__init__(self, config_file)
        self.router = None
        self.events = None
        self.factories = {}

    @defer.inlineCallbacks
    def prepareService(self):
        # Configure ZeroMQ router
        self.router = Router(self)

        # Configure event manager
        self.events = EventManager(self)
        self.events.register_event_handler(self)

        servers = yield self.config.enumerate_servers()

        if not servers:
            log.msg('Warning: No server configurations defined.')

        # Set up client connections
        for server in servers:
            server_config = yield self.config.get_section('server', server, None)
            factory = ClientFactory(self, server, server_config)
            self.factories[server] = factory

            server_hostname = server_config['hostname']
            server_port = server_config.get('port', DEFAULT_PORT)
            server_ssl = server_config.get('ssl', False)
            if not server_ssl:
                connector = internet.TCPClient(server_hostname, server_port, factory)
            else:
                ctx = ssl.ClientContextFactory()
                connector = internet.SSLClient(server_hostname, server_port, factory, ctx)
            connector.setServiceParent(self)

    def _get_client(self, server):
        factory = self.factories.get(server)
        if factory is None:
            log.msg('Received message request for unknown server \'%s\'.' % server)
            return None

        if not factory.client:
            log.msg('Received message request for currently disconnected server \'%s\'.' % server)
            return None

        return factory.client

    def message(self, server_name, user, message):
        client = self._get_client(server_name)
        if client is None:
            return

        return client.msg(user, message)

    def join(self, server_name, channel, key=None):
        client = self._get_client(server_name)
        if client is None:
            return

        return client.join(channel, key)

    def leave(self, server_name, channel, reason=None):
        client = self._get_client(server_name)
        if client is None:
            return

        return client.leave(channel, reason)

    def nick(self, server_name, nickname):
        client = self._get_client(server_name)
        if client is None:
            return

        return client.setNick(nickname)

    def action(self, server_name, channel, action):
        client = self._get_client(server_name)
        if client is None:
            return

        return client.describe(channel, action)
