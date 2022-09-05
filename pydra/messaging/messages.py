from .base import PydraMessage
from .serializers import serialize_string, serialize_float

import numpy as np
import time


StringMessage = type("StringMessage", (PydraMessage,), {"flag": b"string"})
STRING = StringMessage(str)

EventMessage = type("EventMessage", (PydraMessage,), {"flag": b"event"})
EVENT = EventMessage(str, dict)

TriggerMessage = type("TriggerMessage", (PydraMessage,), {"flag": b"trigger"})
TRIGGER = TriggerMessage()


class DataMessage(PydraMessage):
    """Decorator for sending data. Takes a data_flag as an argument for specifying the format of the data being sent."""

    flag = b"data"

    dtypes = {
        b"t": (float, dict),
        b"i": (float, int, dict),
        b"a": (float, int, np.ndarray),
        b"f": (float, int, np.ndarray),
        b"o": (object,)
    }

    def __init__(self, data_flag):
        super().__init__(*self.dtypes[data_flag])
        self.data_flags = data_flag

    def message_tags(self, obj):
        source = serialize_string(obj.name)
        t = time.time()
        t = serialize_float(t)
        return [self.flag, source, t, self.data_flags]


DATA = DataMessage(b"o")
TIMESTAMPED = DataMessage(b"t")
INDEXED = DataMessage(b"i")
ARRAY = DataMessage(b"a")
FRAME = DataMessage(b"f")


ExitMessage = type("ExitMessage", (PydraMessage,), {"flag": b"exit"})
EXIT = ExitMessage()

LogErrorMessage = type("LogErrorMessage", (PydraMessage,), {"flag": b"error"})
ERROR = LogErrorMessage(object, str)

ConnectionMessage = type("ConnectionMessage", (PydraMessage,), {"flag": b"connection"})
CONNECTION = ConnectionMessage(bool)
