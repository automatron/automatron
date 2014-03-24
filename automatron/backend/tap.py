from twisted.python import usage
from automatron.backend.controller import BackendController


class Options(usage.Options):
    optParameters = [
        ['config', 'C', 'automatron.ini', 'Configuration file'],
    ]


def makeService(options):
    return BackendController(options['config'])
