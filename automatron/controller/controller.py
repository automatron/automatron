from ConfigParser import SafeConfigParser

from twisted.application import internet
from twisted.application.service import MultiService
from twisted.internet import defer
from twisted.plugin import getPlugins
from twisted.python import log

from automatron.controller.client import ClientFactory
from automatron.controller.config import IAutomatronConfigManagerFactory
from automatron.controller.plugin import PluginManager


DEFAULT_PORT = 6667


class Controller(MultiService):
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
