from ConfigParser import NoSectionError
import cPickle
from twisted.plugin import IPlugin, getPlugins
from twisted.python import log
from txzmq import ZmqFactory, ZmqEndpoint, ZmqPubConnection
import zope.interface
import zope.interface.verify
from automatron.controller.router import DEFAULT_SUB_ENDPOINT
from automatron.core.event import EventManager


class IAutomatronPluginFactory(IPlugin):
    def __call__(controller):
        """
        Create a new controller.
        """


class PluginManager(EventManager):
    def __init__(self, controller):
        super(PluginManager, self).__init__(controller)
        self.load_plugins()

        try:
            config = self.controller.config_file.items('router')
        except NoSectionError:
            config = {}
        zmq_factory = ZmqFactory()
        sub_endpoint = ZmqEndpoint('connect', config.get('sub-endpoint', DEFAULT_SUB_ENDPOINT))
        self.zmq_pub = ZmqPubConnection(zmq_factory, sub_endpoint)

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
        tag = '%s.%s' % (event.interface.getName(), event.getName())
        self.zmq_pub.publish(cPickle.dumps(args), tag)

    def emit_internal(self, event, *args):
        tag = '%s.%s' % (event.interface.getName(), event.getName())
        self.dispatch_event(tag, *args)
