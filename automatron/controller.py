from ConfigParser import SafeConfigParser
from twisted.application import internet
from twisted.application.service import MultiService
from twisted.enterprise import adbapi
from automatron.client import ClientFactory
from automatron.plugin import PluginManager


DEFAULT_PORT = 6667


class Controller(object):
    def __init__(self, config_file):
        self.config_file = config_file

        # Load configuration file
        self.config = SafeConfigParser()
        self.config.readfp(open(config_file))

        # Set up the database connection pool
        db_section = dict(self.config.items('database'))
        dbapi_name = db_section.pop('dbapi')
        self.database = adbapi.ConnectionPool(dbapi_name, **db_section)
      
        # Load plugins
        self.plugins = PluginManager(self)
    
    def find_config_section(self, *pieces):
        for i in range(1, len(pieces) + 1):
            section = '.'.join(['%s'] * i) % pieces[:i]
            if self.config.has_section(section):
                return section

    def __call__(self):
        service = MultiService()

        for server in self.config.get('automatron', 'servers').split(','):
            server = server.strip()
            if not server:
                continue
            server_section = 'server.%s' % server
            server_config = dict(self.config.items(server_section))
            factory = ClientFactory(self, server, server_config)

            server_hostname = self.config.get(server_section, 'hostname')
            if self.config.has_option(server_section, 'port'):
                server_port = self.config.getint(server_section, 'port')
            else:
                server_port = DEFAULT_PORT
            connector = internet.TCPClient(server_hostname, server_port, factory)
            connector.setServiceParent(service)

        return service
