from twisted.plugin import IPlugin, getPlugins
from twisted.python import log
import zope.interface
import zope.interface.verify
from automatron.core.event import EventManager


class IAutomatronPluginFactory(IPlugin):
    name = zope.interface.Attribute("""The name of this plugin.""")
    priority = zope.interface.Attribute("""The priority with which the plugin will be executed.""")

    def __call__(controller):
        """
        Create a new controller.
        """


class PluginManager(EventManager):
    def __init__(self, controller):
        super(PluginManager, self).__init__(controller)
        self.load_plugins()

    def load_plugins(self):
        plugin_classes = list(getPlugins(IAutomatronPluginFactory))
        for plugin_class in plugin_classes:
            try:
                zope.interface.verify.verifyObject(IAutomatronPluginFactory, plugin_class)
            except (zope.interface.verify.BrokenImplementation, zope.interface.verify.BrokenMethodImplementation) as e:
                log.err(e, 'Plugin %s is broken' % plugin_class.__name__)
                continue
            self.register_event_handler(plugin_class(self.controller))

    def emit(self, event, *args):
        interface_event_name = '%s.%s' % (event.interface.getName(), event.getName())
        super(PluginManager, self).emit(interface_event_name, *args)
