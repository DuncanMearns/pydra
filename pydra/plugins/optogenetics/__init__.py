from ..plugin import Plugin
from .protocol import OptogeneticsProtocol
from .widget import OptogeneticsWidget


class Optogenetics(Plugin):

    protocol = OptogeneticsProtocol
    widget = OptogeneticsWidget

    def __init__(self, pipeline):
        super().__init__(pipeline)
