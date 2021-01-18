import time
from pydra.core import Saver, messaging, PydraObject
from pydra.core.messaging import *
from pathlib import Path
import os
import sys


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
    modules = []

    @classmethod
    def run(cls):
        global config
        global ports
        # Add modules
        cls.modules = config["modules"]
        # Configure saver connections
        pydra_port = config["connections"]["pydra"]["port"]
        config["connections"]["saver"]["subscriptions"].append(("pydra", pydra_port, (EXIT, EVENT, LogMessage)))
        # Configure connections
        for module in cls.modules:
            worker = module["worker"]
            worker_config = {}
            pub, sub = ports.pop(0)
            worker_config["publisher"] = pub
            worker_config["port"] = sub
            worker_config["subscriptions"] = [("pydra",
                                               pydra_port,
                                               (EXIT, EVENT))]
            config["connections"][worker.name] = worker_config
        # Add subscriptions to saver and workers
        for module in cls.modules:
            worker = module["worker"]
            port = config["connections"][worker.name]["port"]
            config["connections"]["saver"]["subscriptions"].append((worker.name, port, (TextMessage, LogMessage, DataMessage)))
            for name in worker.subscriptions:
                port = config["connections"][name]["port"]
                config["connections"][worker.name]["subscriptions"].append((worker.name, port, (EVENT, DataMessage)))
        # Return pydra object
        return cls(**config)

    def __init__(self, *args, **kwargs):
        # Initialize main
        super().__init__(*args, **kwargs)
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
        self.saver = Saver.start(groups, None, zmq_config=kwargs["zmq_config"])
        # Wait for saver
        self.zmq_receiver.recv_multipart()
        print("Saver ready.\nStarting modules...")
        # Start workers
        for module in self.modules:
            module["worker"].start(zmq_config=kwargs["zmq_config"], **module["params"])
        # Wait for processes to start
        self.test_connections()
        # Set working directory and filename
        working_dir = kwargs.get("working_dir", os.getcwd())
        self.working_dir = Path(working_dir)
        filename = kwargs.get("filename", "default_filename")
        self.filename = filename

    @EXIT
    def exit(self):
        return ()

    @EVENT
    def start_recording(self):
        return "start_recording", dict(directory=str(self.working_dir), filename=str(self.filename))

    @EVENT
    def stop_recording(self):
        return "stop_recording", {}

    @LOGGED
    @EVENT
    def set_working_directory(self, directory):
        self.working_dir = directory
        return "set_working_directory", dict(directory=str(self.working_dir))

    @LOGGED
    @EVENT
    def set_filename(self, filename):
        self.filename = filename
        return "set_filename", dict(filename=str(self.filename))

    def query(self, query_type):
        self.send_event("query", query_type=query_type)
        result = self.zmq_receiver.recv_multipart()
        return result[:-1]

    @staticmethod
    def parse_logdata(log):
        return [messaging.LOGINFO.decode(*log[(4 * i):(4 * i) + 4]) for i in range(len(log) // 4)]

    def request_log(self):
        log = self.query("log")
        if len(log):
            log = self.parse_logdata(log)
            return True, log
        return False, log

    def request_events(self):
        events = self.query("events")
        if len(events):
            event_data = self.parse_logdata(events)
            return True, event_data
        return False, events

    def test_connections(self, timeout=10.):
        print("Testing connections...")
        t0 = time.time()
        t1 = t0 + timeout
        connected = dict([(module["name"], False) for module in self.modules])
        while (time.time() < t1) and (not all(connected.values())):
            time.sleep(0.1)
            self.send_event("test_connection")
            ret, events = self.request_events()
            if ret:
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
            for module in filter(lambda x: not connected[x], connected):
                print(f"Module {module} did not respond within {timeout} seconds. Check ZMQ config file.")

    def receive_events(self):
        events = self.query("events")
        events = self.parse_logdata(events)
        for (t, source, event, kwargs) in events:
            if event in self.events:
                self.events[event](**kwargs)
