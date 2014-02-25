from twisted.plugin import IPlugin
import zope.interface


class IAutomatronConfigManagerFactory(IPlugin):
    def __call__(controller):
        """
        Create a new configuration manager.
        """

    name = zope.interface.Attribute("""The name of this Configuration Manager.""")


class IConfigManager(zope.interface.Interface):
    def prepare():
        """
        Establish the database connection.
        """

    def enumerate_servers():
        """
        Return a list of servers for which we have configuration.
        """

    def get_section(section, server, channel):
        """
        Get a complete configuration for a specific channel on a server
        in a section. This should also contain inherited settings.
        """

    def get_plugin_section(plugin, server, channel):
        """
        Convenience method to obtain a configuration section for a plugin.
        """

    def get_value(section, server, channel, key):
        """
        Return a configuration value and its relevance. If relevance is 0
        the value is a global value, if relevance is 1 it is set at server
        level, if relevance is 2 it is set on channel (but not server) level,
        if relevance is 3 it is specific to both server and channel.
        """

    def get_plugin_value(plugin, server, channel, key):
        """
        Convenience method to obtain a configuration value for a plugin.
        """

    def update_value(section, server, channel, key, new_value):
        """
        Update or set a configuration value. Note that the relevance will remain
        the same as it was if it was already set.
        """

    def update_plugin_value(plugin, server, channel, key, new_value):
        """
        Convenience method to update or set a configuration value for a plugin.
        """

    def get_username_by_hostmask(server, user):
        """
        Given a full IRC username (<nickname>!<username>@host), retrieve the
        registered system username for a given server.
        """

    def get_role_by_username(server, channel, username):
        """
        Given a system username, retrieve the role the user has in a certain
        channel.
        """

    def get_permissions_by_role(role):
        """
        Given a role, determine the permissions that this role is granted.
        """

    def has_permission(server, channel, user, permission):
        """
        Check whether an IRC user has a specific permission in a channel.
        """

    def get_user_preference(server, username, preference):
        """
        Retrieve a user preference for a given system username.
        """

    def update_user_preference(server, username, preference, value):
        """
        Store a user preference for a given system username.
        """
