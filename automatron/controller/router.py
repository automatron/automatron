from ConfigParser import NoSectionError
import cPickle
from txzmq import ZmqFactory, ZmqEndpoint, ZmqPubConnection, ZmqSubConnection


DEFAULT_PUB_ENDPOINT = 'tcp://127.0.0.1:5555'
DEFAULT_SUB_ENDPOINT = 'tcp://127.0.0.1:5556'


class Router(object):
    def __init__(self, controller):
        self.controller = controller

        try:
            config = self.controller.config_file.items('router')
        except NoSectionError:
            config = {}

        zmq_factory = ZmqFactory()

        pub_endpoint = ZmqEndpoint('bind', config.get('pub-endpoint', DEFAULT_PUB_ENDPOINT))
        self.zmq_pub = ZmqPubConnection(zmq_factory, pub_endpoint)

        sub_endpoint = ZmqEndpoint('bind', config.get('sub-endpoint', DEFAULT_SUB_ENDPOINT))
        self.zmq_sub = ZmqSubConnection(zmq_factory, sub_endpoint)
        self.zmq_sub.gotMessage = self.forward
        self.zmq_sub.subscribe("")

    def publish(self, event, *args):
        tag = '%s.%s' % (event.interface.getName(), event.getName())
        self.zmq_pub.publish(cPickle.dumps(args), tag)

    def forward(self, message, tag):
        self.zmq_pub.publish(message, tag)
