from .base import *
import zmq


class PydraMain(PydraPublisher, PydraReceiver):

    name = "pydra"

    def __init__(self, connections: dict):
        self.connections = connections[self.name]
        super().__init__(**self.connections)

    @staticmethod
    def destroy():
        """Destroys the 0MQ context."""
        zmq.Context.instance().destroy(200)
