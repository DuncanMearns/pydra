from .base import PydraObject
from .process import ProcessMixIn
from .messaging import EXIT, EVENT, LOGGED


class Worker(PydraObject, ProcessMixIn):
    """Base worker class. Receives and handles messages. Runs in a separate process."""

    name = "worker"
    subscriptions = []

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        if cls.name not in zmq_config:
            zmq_config[cls.name] = {}
        try:
            # Add a port for publishing outputs
            if "publisher" not in zmq_config[cls.name]:
                zmq_config[cls.name]["publisher"] = ports.pop(0)
            # Add subscriptions to config
            zmq_config[cls.name]["subscriptions"] = []
            # Add subscription to main pydra process
            subscribe_to_main = ("pydra", zmq_config["pydra"]["publisher"][1], (EVENT, EXIT))
            zmq_config[cls.name]["subscriptions"].append(subscribe_to_main)
            for name, port, messages in subscriptions:
                if name in zmq_config:
                    port = zmq_config[name]["publisher"][1]
                zmq_config[cls.name]["subscriptions"].append((name, port, messages))
        except IndexError:
            print(f"Not enough ports to configure {cls.name}")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events["test_connection"] = self.check_connection
        self._connected = 0

    def _process(self):
        """Handles all messages received over network from 0MQ."""
        self.poll()

    def check_connection(self, **kwargs):
        """Called by the 'test_connection' event. Informs pydra that 0MQ connections have been established and worker is
        receiving messages."""
        if not self._connected:
            self._connected = 1
            self.connected()

    @LOGGED
    def connected(self):
        return dict(event=True)

    def exit(self, *args, **kwargs):
        """Sets the exit_flag when EXIT signal is received, causing process to terminate ."""
        self.close()


class Acquisition(Worker):
    """Base worker class for acquiring data. Implements an independent acquire method after checking for messages."""

    name = "acquisition"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _process(self):
        """Checks for messages received over network from 0MQ, then calls the acquire method."""
        super()._process()
        self.acquire()

    def acquire(self):
        return


class RemoteReceiver(Worker):

    name = "receiver"

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        try:
            assert "receiver" in zmq_config[cls.name]
        except AssertionError:
            raise ValueError(f"zmq_config for {cls.name} must contain a 'receiver' key")
        super(RemoteReceiver, cls).configure(zmq_config, ports, subscriptions)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def poll_remote(self):
        ret = self.zmq_receiver.poll(0)
        if ret:
            parts = self.zmq_receiver.recv_multipart()
            self.recv_remote(*parts)

    def recv_remote(self, *args):
        return

    def _process(self):
        self.poll_remote()
        super()._process()


class RemoteSender(Worker):

    name = "sender"

    @classmethod
    def configure(cls, zmq_config, ports, subscriptions=()):
        # Create dictionary for storing config info
        try:
            assert "sender" in zmq_config[cls.name]
        except AssertionError:
            raise ValueError(f"zmq_config for {cls.name} must contain a 'sender' key")
        super(RemoteSender, cls).configure(zmq_config, ports, subscriptions)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
