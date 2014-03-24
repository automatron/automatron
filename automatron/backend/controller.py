from automatron.backend.plugin import PluginManager
from automatron.core.controller import BaseController


class BackendController(BaseController):
    def __init__(self, config_file):
        BaseController.__init__(self, config_file)
        self.plugins = None

    def prepareService(self):
        # Load plugins
        self.plugins = PluginManager(self)
