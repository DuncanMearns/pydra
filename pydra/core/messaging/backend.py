from .base import PydraMessage, PushMessage

__all__ = ("EXIT", "CONNECTION", "ERROR", "REQUEST", "_CONNECTION", "_DATA", "_ERROR")

ExitMessage = type("ExitMessage", (PydraMessage,), {"flag": b"exit"})
EXIT = ExitMessage()

ConnectionMessage = type("ConnectionMessage", (PydraMessage,), {"flag": b"connection"})
CONNECTION = ConnectionMessage(bool)

LogErrorMessage = type("LogErrorMessage", (PydraMessage,), {"flag": b"error"})
ERROR = LogErrorMessage(object, str)

RequestMessage = type("RequestMessage", (PydraMessage,), {"flag": b"request"})
REQUEST = RequestMessage(str)

BEConnectionMessage = type("BEConnectionMessage", (PushMessage,), {"flag": b"_connection"})
_CONNECTION = BEConnectionMessage(bool)

BEDataMessage = type("BEDataMessage", (PushMessage,), {"flag": b"_data"})
_DATA = BEDataMessage()

BEErrorMessage = type("BEErrorMessage", (PushMessage,), {"flag": b"_error"})
_ERROR = BEErrorMessage(object, str)

# class LoggedMessage(PydraMessage):
#     """Decorator for logging events."""
#
#     flag = b"log"
#
#     def __init__(self):
#         super().__init__(str, dict)
#
#     def serializer(self, args):
#         obj, method, result = args
#         name = method.__name__
#         out = self.message_tags(obj)
#         out += self.encode(name, result)
#         return out
#
#
# LOGGED = LoggedMessage()
#
# # INFO message for sending event info between saver and pydra
# EVENT_INFO = PydraMessage(float, str, str, dict, np.ndarray)
# # INFO message for sending data info between saver and pydra
# DATA_INFO = PydraMessage(str, dict, np.ndarray)
