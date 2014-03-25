import shlex

from twisted.internet import defer
from twisted.python import log
from zope.interface import implements, classProvides

from automatron.backend.command import IAutomatronCommandHandler
from automatron.backend.plugin import IAutomatronPluginFactory
from automatron.controller.client import IAutomatronMessageHandler
from automatron.core.event import STOP


class CommandMessagePlugin(object):
    classProvides(IAutomatronPluginFactory)
    implements(IAutomatronMessageHandler)

    name = 'command'
    priority = 100

    def __init__(self, controller):
        self.controller = controller

    def on_message(self, server, user, channel, message):
        if channel == server['nickname'] and message:
            return self._on_message(server, user, message)

    @defer.inlineCallbacks
    def _on_message(self, server, user, message):
        try:
            args = shlex.split(message)
        except ValueError as e:
            self.controller.message(server['server'], user, 'Invalid syntax: %s' % str(e))
            log.err(e, 'Unable to parse command')
            defer.returnValue(STOP)

        if not args:
            return
        command = args.pop(0)

        defer.returnValue((yield self.controller.plugins.emit(
            IAutomatronCommandHandler['on_command'],
            server,
            user,
            command,
            args
        )))
