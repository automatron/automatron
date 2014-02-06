from twisted.python import usage
from automatron.controller import Controller


class Options(usage.Options):
    optParameters = [
        ['config', 'C', 'automatron.ini', 'Configuration file'],
    ]


def makeService(options):
    controller = Controller(options['config'])
    return controller()
