from ...core.plugin import Plugin
from .protocol import OptogeneticsProtocol
from .widget import OptogeneticsWidget


class Optogenetics(Plugin):

    worker = OptogeneticsProtocol
    widget = OptogeneticsWidget
