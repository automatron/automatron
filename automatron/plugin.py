from twisted.internet import defer
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
                log.err(e, 'Plugin %s is broken' % plugin_class.__name__)
                continue
            for event_interface in zope.interface.implementedBy(plugin_class):
                if event_interface.extends(IAutomatronEventHandler):
                    try:
                        zope.interface.verify.verifyClass(event_interface, plugin_class)
                    except zope.interface.verify.BrokenMethodImplementation as e:
                        log.err(e, 'Plugin %s is broken' % plugin_class.__name__)
                        break
            else:
                plugins.append(plugin_class(self.controller))
                log.msg('Loaded plugin %s' % plugin_class.name)
        self.plugins = sorted(plugins, key=lambda i: i.priority)

    @defer.inlineCallbacks
    def emit(self, event, *args):
        event_interface = event.interface
        if not event_interface.extends(IAutomatronEventHandler):
            log.msg('Emitted event %s\'s interface (%s) does not extend IAutomatronEventHandler' %
                    (event.getName(), event_interface))
            return

        if len(args) < len(event.required):
            log.msg('Emitted event %s\'s declaration requires at least %d arguments, only %d were '
                    'provided.' % (event.getName(), len(event.required), len(args)))
            return

        if len(args) > len(event.positional):
            log.msg('Emitted event %s\'s declaration requires at most %d arguments, %d were '
                    'provided.' % (event.getName(), len(event.positional), len(args)))
            return

        for plugin in self.plugins:
            try:
                plugin_adapter = event_interface(plugin)
            except TypeError:
                continue

            f = getattr(plugin_adapter, event.getName())
            if (yield defer.maybeDeferred(f, *args)) is STOP:
                defer.returnValue(STOP)
