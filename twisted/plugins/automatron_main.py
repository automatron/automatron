# You can run this with twistd automatron -c <config file>

from twisted.application.service import ServiceMaker

service = ServiceMaker(
    'Automatron IRC bot',
    'automatron.tap',
    'An extendable IRC automaton',
    'automatron'
)
