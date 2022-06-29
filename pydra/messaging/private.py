from .base import PydraMessage, PushMessage

__all__ = ("EXIT", "ERROR", "CONNECTION", "REQUEST", "BACKEND")

ExitMessage = type("ExitMessage", (PydraMessage,), {"flag": b"exit"})
EXIT = ExitMessage()

LogErrorMessage = type("LogErrorMessage", (PydraMessage,), {"flag": b"error"})
ERROR = LogErrorMessage(object, str)

ConnectionMessage = type("ConnectionMessage", (PydraMessage,), {"flag": b"connection"})
CONNECTION = ConnectionMessage(bool)

RequestMessage = type("RequestMessage", (PydraMessage,), {"flag": b"request"})
REQUEST = RequestMessage(str)

BEConnectionMessage = type("BEConnectionMessage", (PushMessage,), {"flag": b"_connection"})
BEDataMessage = type("BEDataMessage", (PushMessage,), {"flag": b"_data"})
BEErrorMessage = type("BEErrorMessage", (PushMessage,), {"flag": b"_error"})
ForwardMessage = type("ForwardMessage", (PushMessage,), {"flag": b"_forward"})


class BACKEND:

    CONNECTION = BEConnectionMessage(bool)
    DATA = BEDataMessage(object)
    ERROR = BEErrorMessage(object, str)
    FORWARD = ForwardMessage(bytes, dict)
