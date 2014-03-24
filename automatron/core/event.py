from twisted.internet import defer
from twisted.python import log
import zope.interface
import zope.interface.verify


STOP = object()


class IAutomatronEventHandler(zope.interface.Interface):
    """
    Abstract interface which is the base of all event handler interfaces.
    """


class EventManager(object):
    def __init__(self, controller):
        self.controller = controller
        self.event_handlers = []

    def register_event_handler(self, handler):
        for event_interface in zope.interface.providedBy(handler):
            if event_interface.extends(IAutomatronEventHandler):
                try:
                    zope.interface.verify.verifyObject(event_interface, handler)
                except (zope.interface.verify.BrokenImplementation,
                        zope.interface.verify.BrokenMethodImplementation) as e:
                    log.err(e, 'Event handler %s is broken' % handler.__name__)
                    break
        else:
            self.event_handlers.append(handler)
            log.msg('Loaded event handler %s' % handler.name)

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

        event_handlers = sorted(self.event_handlers, key=lambda i: i.priority)
        for plugin in event_handlers:
            try:
                event_handler_adapter = event_interface(plugin)
            except TypeError:
                continue

            f = getattr(event_handler_adapter, event.getName())
            if (yield defer.maybeDeferred(f, *args)) is STOP:
                defer.returnValue(STOP)
