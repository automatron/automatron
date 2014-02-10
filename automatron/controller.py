from ConfigParser import SafeConfigParser
from twisted.application import internet
from twisted.application.service import MultiService
from twisted.enterprise import adbapi
from twisted.internet import defer
from twisted.python import log
from automatron.client import ClientFactory
from automatron.plugin import PluginManager


DEFAULT_PORT = 6667


class Controller(MultiService):
    def __init__(self, config_file):
        MultiService.__init__(self)
        self.database = None
        self.plugins = None

        # Load configuration file
        self.config = SafeConfigParser()
        self.config.readfp(open(config_file))

    @defer.inlineCallbacks
    def startService(self):
        # Set up the database connection pool
        db_section = dict(self.config.items('database'))
        dbapi_name = db_section.pop('dbapi')
        self.database = adbapi.ConnectionPool(dbapi_name, **db_section)

        # Load plugins
        self.plugins = PluginManager(self)

        # Find servers to connect to
        result = yield self.database.runQuery(
            '''
                SELECT
                    DISTINCT server
                FROM
                    config
                WHERE
                    section = 'server'
                    AND server IS NOT NULL
                    AND channel IS NULL
                    AND key = 'hostname'
                    AND value IS NOT NULL
            '''
        )
        servers = [s[0] for s in result]

        if not servers:
            log.msg('Warning: No server configurations defined.')

        # Set up client connections
        for server in servers:
            server_config = yield self.get_config_section('server', server, None)
            factory = ClientFactory(self, server, server_config)

            server_hostname = server_config['hostname']
            server_port = server_config.get('port', DEFAULT_PORT)
            connector = internet.TCPClient(server_hostname, server_port, factory)
            connector.setServiceParent(self)

        MultiService.startService(self)

    @defer.inlineCallbacks
    def get_config_section(self, section, server, channel):
        q = ["""
            SELECT
                key,
                value,
                CASE
                    WHEN channel IS NOT NULL AND server IS NOT NULL THEN 3
                    WHEN channel IS NOT NULL THEN 2
                    WHEN server IS NOT NULL THEN 1
                    ELSE 0
                END AS relevance
            FROM
                config
            WHERE
                section = %s
        """]
        args = [section]

        if server is not None:
            q.append('AND (server IS NULL OR server = %s)')
            args.append(server)
        else:
            q.append('AND server IS NULL')

        if channel is not None:
            q.append('AND (channel IS NULL OR channel = %s)')
            args.append(channel)
        else:
            q.append('AND channel IS NULL')

        q.append('ORDER BY relevance ASC')

        result = yield self.database.runQuery(' '.join(q), args)

        section = {}
        for key, val, relevance in result:
            section[key] = val

        defer.returnValue(section)

    @defer.inlineCallbacks
    def get_config_value(self, section, server, channel, key):
        q = ["""
            SELECT
                value,
                CASE
                    WHEN channel IS NOT NULL AND server IS NOT NULL THEN 3
                    WHEN channel IS NOT NULL THEN 2
                    WHEN server IS NOT NULL THEN 1
                    ELSE 0
                END AS relevance
            FROM
                config
            WHERE
                section = %s
                AND key = %s
        """]
        args = [section, key]

        if server is not None:
            q.append('AND (server IS NULL OR server = %s)')
            args.append(server)
        else:
            q.append('AND server IS NULL')

        if channel is not None:
            q.append('AND (channel IS NULL OR channel = %s)')
            args.append(channel)
        else:
            q.append('AND channel IS NULL')

        q.append('ORDER BY relevance DESC LIMIT 1')

        result = yield self.database.runQuery(' '.join(q), args)
        if result:
            defer.returnValue(result[0])
        else:
            defer.returnValue((None, None))

    def get_plugin_config_value(self, plugin, server, channel, key):
        return self.get_config_value('plugin.%s' % plugin.name, server, channel, key)
