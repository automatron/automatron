from twisted.python import usage
from automatron.controller.controller import Controller


class Options(usage.Options):
    optParameters = [
        ['config', 'C', 'automatron.ini', 'Configuration file'],
    ]


def makeService(options):
    return Controller(options['config'])
