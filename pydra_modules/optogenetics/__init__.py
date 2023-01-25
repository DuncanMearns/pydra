from .worker import OptogeneticsWorker
from .widget import OptogeneticsWidget
from pydra import PydraModule, CSVSaver


OPTOGENETICS = PydraModule(worker=OptogeneticsWorker, saver=CSVSaver, widget=OptogeneticsWidget)
