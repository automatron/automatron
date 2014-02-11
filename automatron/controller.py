from twisted.application import internet
from twisted.application.service import MultiService
from twisted.internet import defer
from twisted.python import log
from automatron.client import ClientFactory
from automatron.config import ConfigManager
from automatron.plugin import PluginManager


DEFAULT_PORT = 6667


class Controller(MultiService):
    def __init__(self, config_file):
        MultiService.__init__(self)
        self.config_file = config_file
        self.plugins = None
        self.config = None

    @defer.inlineCallbacks
    def startService(self):
        # Set up configuration manager
        self.config = ConfigManager(self.config_file)

        # Load plugins
        self.plugins = PluginManager(self)

        servers = yield self.config.enumerate_servers()

        if not servers:
            log.msg('Warning: No server configurations defined.')

        # Set up client connections
        for server in servers:
            server_config = yield self.config.get_section('server', server, None)
            factory = ClientFactory(self, server, server_config)

            server_hostname = server_config['hostname']
            server_port = server_config.get('port', DEFAULT_PORT)
            connector = internet.TCPClient(server_hostname, server_port, factory)
            connector.setServiceParent(self)

        MultiService.startService(self)
