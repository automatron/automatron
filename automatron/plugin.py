import sys
from twisted.plugin import getPlugins, IPlugin
from twisted.python import log
import zope.interface
import zope.interface.verify


class IAutomatronPluginFactory(IPlugin):
    name = zope.interface.Attribute("""The name of this plugin.""")
    priority = zope.interface.Attribute("""The priority with which the plugin will be executed.""")

    def __call__(controller):
        """
        Create a new controller.
        """


class IAutomatronEventHandler(zope.interface.Interface):
    """
    Abstract interface which is the base of all event handler interfaces.
    """


STOP = object()


class PluginManager(object):
    def __init__(self, controller):
        self.controller = controller
        self.plugins = []
        self.reload()

    def reload(self):
        plugins = []
        plugin_classes = list(getPlugins(IAutomatronPluginFactory))
        for plugin_class in plugin_classes:
            try:
                zope.interface.verify.verifyObject(IAutomatronPluginFactory, plugin_class)
            except (zope.interface.verify.BrokenImplementation, zope.interface.verify.BrokenMethodImplementation) as e:
                print >>sys.stderr, 'Invalid plugin: %s' % plugin_class.__name__
                print >>sys.stderr, e
                continue
            for iface in zope.interface.implementedBy(plugin_class):
                if iface.extends(IAutomatronEventHandler):
                    try:
                        zope.interface.verify.verifyClass(iface, plugin_class)
                    except zope.interface.verify.BrokenMethodImplementation as e:
                        print >>sys.stderr, 'Invalid plugin: %s' % plugin_class
                        print >>sys.stderr, e
                        break
            else:
                plugins.append(plugin_class(self.controller))
        self.plugins = sorted(plugins, key=lambda i: i.priority)

    def emit(self, event, *args):
        method = 'on_%s' % event
        for plugin in self.plugins:
            for iface in zope.interface.providedBy(plugin):
                if iface.extends(IAutomatronEventHandler) and method in iface:
                    f = getattr(plugin, method)
                    if f(*args) is STOP:
                        break
