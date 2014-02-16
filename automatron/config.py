from ConfigParser import SafeConfigParser
from twisted.enterprise import adbapi
from twisted.internet import defer


class ConfigManager(object):
    def __init__(self, config_file):
        # Load configuration file
        config = SafeConfigParser()
        config.readfp(open(config_file))

        # Set up the database connection pool
        db_section = dict(config.items('database'))
        dbapi_name = db_section.pop('dbapi')
        self.database = adbapi.ConnectionPool(dbapi_name, **db_section)

    @defer.inlineCallbacks
    def enumerate_servers(self):
        defer.returnValue([
            s[0]
            for s in (yield self.database.runQuery(
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
            ))
        ])

    @defer.inlineCallbacks
    def get_section(self, section, server, channel):
        q = """
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
                AND (server IS NULL OR server = %s)
                AND (channel IS NULL OR channel = %s)
            ORDER BY
                relevance ASC
        """
        result = yield self.database.runQuery(q, (section, server, channel))

        section = {}
        for key, val, relevance in result:
            section[key] = val

        defer.returnValue(section)

    def get_plugin_section(self, plugin, server, channel):
        return self.get_section('plugin.%s' % plugin.name, server, channel)

    @defer.inlineCallbacks
    def get_value(self, section, server, channel, key):
        q = """
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
                AND (server IS NULL OR server = %s)
                AND (channel IS NULL OR channel = %s)
                AND key = %s
            ORDER BY
                relevance DESC
            LIMIT 1
        """
        result = yield self.database.runQuery(q, (section, server, channel, key))

        if result:
            defer.returnValue(result[0])
        else:
            defer.returnValue((None, None))

    def get_plugin_value(self, plugin, server, channel, key):
        return self.get_value('plugin.%s' % plugin.name, server, channel, key)

    @defer.inlineCallbacks
    def update_value(self, section, server, channel, key, new_value):
        _, relevance = yield self.get_value(section, server, channel, key)
        if relevance is not None:
            if relevance == 2:
                server = None
            elif relevance == 1:
                channel = None
            elif relevance == 0:
                server = channel = None

            q = ["""
                UPDATE
                    config
                SET
                    value = %s
                WHERE
                    section = %s
                    AND key = %s
            """]
            params = [new_value, section, key]

            if server is not None:
                q.append('AND server = %s')
                params.append(server)
            else:
                q.append('AND server IS NULL')

            if channel is not None:
                q.append('AND channel = %s')
                params.append(channel)
            else:
                q.append('AND channel IS NULL')
        else:
            q = ["""
                INSERT INTO
                    config
                    (
                        section,
                        server,
                        channel,
                        key,
                        value
                    )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """]
            params = [section, server, channel, key, new_value]

        self.database.runOperation(' '.join(q), params)

    def update_plugin_value(self, plugin, server, channel, key, new_value):
        return self.update_value('plugin.%s' % plugin.name, server, channel, key, new_value)
