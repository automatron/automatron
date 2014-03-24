from ConfigParser import SafeConfigParser

from twisted.application import internet
from twisted.application.service import MultiService
from twisted.internet import defer
from twisted.plugin import getPlugins
from twisted.python import log
from zope.interface import implements

from automatron.controller.client import ClientFactory
from automatron.controller.config import IAutomatronConfigManagerFactory
from automatron.controller.plugin import PluginManager
from automatron.core.event import IAutomatronEventHandler


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


class Controller(MultiService):
    implements(IAutomatronClientActions)
    priority = 100
    name = 'controller'

    def __init__(self, config_file):
        MultiService.__init__(self)

        self.config_file = SafeConfigParser()
        self.config_file.readfp(open(config_file))

        self.plugins = None
        self.config = None
        self.factories = {}

    @defer.inlineCallbacks
    def startService(self):
        # Set up configuration manager
        self.config = self._build_config_manager()
        yield self.config.prepare()

        # Load plugins
        self.plugins = PluginManager(self)
        self.plugins.register_event_handler(self)

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
            connector = internet.TCPClient(server_hostname, server_port, factory)
            connector.setServiceParent(self)

        MultiService.startService(self)

    def _build_config_manager(self):
        typename = self.config_file.get('automatron', 'configmanager')
        factories = list(getPlugins(IAutomatronConfigManagerFactory))
        for factory in factories:
            if factory.name == typename:
                return factory(self)
        else:
            raise RuntimeError('Config manager class %s not found' % typename)

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
