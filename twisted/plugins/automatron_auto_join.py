from zope.interface import implements, classProvides
from automatron.plugin import IAutomatronPluginFactory
from automatron.client import IAutomatronSignedOnHandler


SECTION = 'plugins.auto_join'


class AutoJoinPlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronSignedOnHandler)

    name = 'auto_join'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_signed_on(self, client):
        section = self.controller.find_config_section(SECTION, client.server)
        if section is None:
            return

        if self.controller.config.has_option(section, 'join'):
            channels = self.controller.config.get(section, 'join').split(',')
            for channel in channels:
                client.join(channel.strip())
