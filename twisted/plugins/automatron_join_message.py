from zope.interface import implements, classProvides
from automatron.plugin import IAutomatronPluginFactory, IAutomatronChannelJoinedHandler


SECTION = 'plugins.join_message'


class JoinMessagePlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronChannelJoinedHandler)

    name = 'join_message'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_channel_joined(self, client, channel):
        section = self.controller.find_config_section(SECTION, client.server, channel)
        if section is None:
            return

        if self.controller.config.has_option(section, 'message'):
            message = self.controller.config.get(section, 'message')
            f = client.msg
        elif self.controller.config.has_option(section, 'action'):
            message = self.controller.config.get(section, 'action')
            f = client.describe
        else:
            return
        
        f(channel, message % {
            'nickname': client.nickname,
            'realname': client.realname,
        })
