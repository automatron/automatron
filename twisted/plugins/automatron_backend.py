# You can run this with twistd automatron-backend -c <config file>

from twisted.application.service import ServiceMaker

service = ServiceMaker(
    'Automatron IRC bot - Plugin backend'
    '',
    'automatron.backend.tap',
    'An extendable IRC automaton',
    'automatron-backend'
)
