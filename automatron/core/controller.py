from ConfigParser import SafeConfigParser
from twisted.application.service import MultiService
from twisted.internet import defer
from twisted.plugin import getPlugins
from automatron.core.config import IAutomatronConfigManagerFactory


class BaseController(MultiService):
    def __init__(self, config_file):
        MultiService.__init__(self)

        self.config_file = SafeConfigParser()
        self.config_file.readfp(open(config_file))

        self.config = None

    @defer.inlineCallbacks
    def startService(self):
        # Set up configuration manager
        self.config = self._build_config_manager()
        yield self.config.prepare()

        yield self.prepareService()

        MultiService.startService(self)

    def prepareService(self):
        pass

    def _build_config_manager(self):
        typename = self.config_file.get('automatron', 'configmanager')
        factories = list(getPlugins(IAutomatronConfigManagerFactory))
        for factory in factories:
            if factory.name == typename:
                return factory(self)
        else:
            raise RuntimeError('Config manager class %s not found' % typename)
