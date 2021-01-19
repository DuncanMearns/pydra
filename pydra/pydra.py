import time
from pydra.core import Saver, PydraObject
from pydra.core.messaging import *
from pathlib import Path
import os


ports = [
    ("tcp://*:5555", "tcp://localhost:5555"),
    ("tcp://*:5556", "tcp://localhost:5556"),
    ("tcp://*:5557", "tcp://localhost:5557"),
    ("tcp://*:5558", "tcp://localhost:5558"),
    ("tcp://*:5559", "tcp://localhost:5559")
]


config = {

    "connections": {

        "pydra": {
            "publisher": "tcp://*:6000",
            "receiver": "tcp://localhost:6001",
            "port": "tcp://localhost:6000"
        },

        "saver": {
            "sender": "tcp://*:6001",
            "subscriptions": []
        },

    },

    "modules": []

}


class Pydra(PydraObject):

    name = "pydra"

    @staticmethod
    def configure(config, ports):
        # Add modules
        modules = config["modules"]
        # Connect saver to pydra
        pydra_port = config["connections"]["pydra"]["port"]
        config["connections"]["saver"]["subscriptions"].append(("pydra", pydra_port, (EXIT, EVENT, LOGGED)))
        # Assign ports to workers
        for module in modules:
            worker = module["worker"]
            worker_config = {}
            pub, sub = ports.pop(0)
            worker_config["publisher"] = pub
            worker_config["port"] = sub
            config["connections"][worker.name] = worker_config
            # Add saver subscription
            config["connections"]["saver"]["subscriptions"].append((worker.name,
                                                                    worker_config["port"],
                                                                    (MESSAGE, LOGGED, DATA)))
        # Add connections for subscriptions
        for module in modules:
            worker = module["worker"]
            # Add subscription to pydra
            config["connections"][worker.name]["subscriptions"] = [("pydra",
                                                                    pydra_port,
                                                                    (EXIT, EVENT))]
            # Add subscriptions to other workers
            for sub in worker.subscriptions:
                port = config["connections"][sub]["port"]
                config["connections"][worker.name]["subscriptions"].append((worker.name,
                                                                            port,
                                                                            (EVENT, DATA)))
        # Return configuration
        return config

    def __init__(self, connections: dict, modules: list = None, *args, **kwargs):
        self.connections = connections
        self.modules = modules
        super().__init__(connections=connections, *args, **kwargs)
        # Start saver
        groups = {}
        for module in self.modules:
            try:
                group = module["group"]
            except KeyError:
                group = ""
            if group in groups:
                groups[group].append(module["name"])
            else:
                groups[group] = [module["name"]]
        # Start saver and wait for it to respond
        self.saver = Saver.start(groups, None, connections=connections)
        self.zmq_receiver.recv_multipart()
        # Start module workers
        print("Saver ready. Starting modules...", end=" ")
        for module in self.modules:
            module["worker"].start(connections=connections, **module["params"])
        print("done.")
        # Test connections to workers
        self.test_connections()
        # Set working directory and filename
        working_dir = kwargs.get("working_dir", os.getcwd())
        self.working_dir = Path(working_dir)
        filename = kwargs.get("filename", "default_filename")
        self.filename = filename

    @EXIT
    def exit(self):
        """Broadcasts an exit signal."""
        return ()

    @EVENT
    def start_recording(self):
        """Broadcasts a start_recording event."""
        return "start_recording", dict(directory=str(self.working_dir), filename=str(self.filename))

    @EVENT
    def stop_recording(self):
        """Broadcasts a start_recording event."""
        return "stop_recording", {}

    @LOGGED
    @EVENT
    def set_working_directory(self, directory):
        """Broadcasts a logged set_working_directory event."""
        self.working_dir = directory
        return "set_working_directory", dict(directory=str(self.working_dir))

    @LOGGED
    @EVENT
    def set_filename(self, filename):
        """Broadcasts a logged set_filename event."""
        self.filename = filename
        return "set_filename", dict(filename=str(self.filename))

    def query(self, query_type: str):
        """General method for sending any request to the saver.

        Parameters
        ----------
        query_type : str
            A specific query that can be fulfilled by the saver.

        See Also
        --------
        pydra.core.saving.Saver
        """
        self.send_event("query", query_type=query_type)
        result = self.zmq_receiver.recv_multipart()
        return result[:-1]

    @staticmethod
    def decode_message(msg):
        """Decode INFO messages from saver."""
        return [INFO.decode(*msg[(4 * i):(4 * i) + 4]) for i in range(len(msg) // 4)]

    def request_log(self):
        """Request info from saver log."""
        log = self.query("log")
        if len(log):
            log = self.decode_message(log)
            return True, log
        return False, log

    def request_events(self):
        """Request info from saver about worker events."""
        events = self.query("events")
        if len(events):
            event_data = self.decode_message(events)
            return True, event_data
        return False, events

    def test_connections(self, timeout=10.):
        """Checks that all workers in the network are receiving messages from pydra.

        Parameters
        ----------
        timeout : float
            Maximum time to wait for workers to respond (seconds)."""
        print("Testing connections...")
        # Get the current time and timeout time
        t0 = time.time()
        t_timeout = t0 + timeout
        # Create a dictionary with the connection status of each worker
        connected = dict([(module["name"], False) for module in self.modules])
        # loop as long as workers are not connected or until the timeout has passed
        while (time.time() < t_timeout) and (not all(connected.values())):
            time.sleep(0.1)
            self.send_event("test_connection")  # send a test_connection event
            ret, events = self.request_events()  # receive logged events
            if ret:
                # check for "connected" events from unconnected workers
                for module in filter(lambda x: not connected[x], connected):
                    module_events = list(filter(lambda x: x[1] == module, events))
                    if len(module_events):
                        event_times, event_names = zip(*[(item[0], item[2]) for item in module_events])
                        if "connected" in event_names:
                            idx = event_names.index("connected")
                            event_time = event_times[idx]
                            print(f"Module {module} responded after {event_time - t0} seconds.")
                            connected[module] = True
        if all(connected.values()):
            print("All modules connected!")
        else:
            for module in filter(lambda x: not connected[x], connected):  # provide diagnostic info for user
                print(f"Module {module} did not respond within {timeout} seconds. Check connections in config.")

    def receive_events(self):
        events = self.query("events")
        events = self.decode_message(events)
        for (t, source, event, kwargs) in events:
            if event in self.events:
                self.events[event](**kwargs)
