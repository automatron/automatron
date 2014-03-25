from automatron.backend.plugin import PluginManager
from automatron.controller.controller import IAutomatronClientActions
from automatron.core.controller import BaseController


class BackendController(BaseController):
    def __init__(self, config_file):
        BaseController.__init__(self, config_file)
        self.plugins = None

    def prepareService(self):
        # Load plugins
        self.plugins = PluginManager(self)

    def __getattr__(self, item):
        def proxy(*args):
            self.plugins.emit(IAutomatronClientActions[item], *args)
        return proxy
