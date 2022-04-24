from .._base import *
from .._base.messaging import PUSH
from ..utils import Parallelized


class PydraQuery(PydraMessage):

    flag = b"query"

    def __init__(self, *dtypes):
        super().__init__(*dtypes)


QUERY = PydraQuery(str)


class QueryMessage(PydraMessage):

    flag = b"qm"

    def __init__(self, *dtypes):
        super().__init__(*dtypes, socktype=PUSH)


QCONNECTED = QueryMessage()
QMESSAGES = QueryMessage()
QEVENTS = QueryMessage()
QDATA = QueryMessage()


class Saver(Parallelized, PydraSubscriber):

    workers = ()
    args = ()
    kwargs = {}
    _connections = {}

    @classmethod
    def start(cls, *args, **kwargs):
        kw = cls.kwargs.copy()
        kw.update(cls._connections)
        return super().start_thread(*cls.args, **kw)

    @classmethod
    def to_tuple(cls):
        return cls, cls.args, cls.kwargs, cls._connections

    # @QCONNECTED
    # def connected(self):
    #     return ()

    def __init__(self, subscriptions, *args, **kwargs):
        super().__init__(subscriptions, *args, **kwargs)

    def _process(self):
        self.poll()

    def recv_timestamped(self, t, data, **kwargs):
        pass

    def recv_indexed(self, t, i, data, **kwargs):
        pass

    def recv_frame(self, t, i, frame, **kwargs):
        pass

    def recv_array(self, t, i, a, **kwargs):
        pass


class PydraBackend(Parallelized, PydraPublisher, PydraSender, PydraSubscriber):
    """Singleton Saver class that integrates and handles incoming messages from all workers.

    Parameters
    ----------
    connections : dict
        Dictionary of workers (as a list of names) assigned to each pipeline (keys). Passed from pydra pipelines
        property.

    Attributes
    ----------
    event_log : list
        Logged messages from pydra objects.
    messages : list
        List of string-type messages received from pydra objects.
    recording : bool
        Stores whether data are currently being saved.
    savers : list
        List that stores all PipelineSaver objects.
    targets : dict
        A dictionary that maps data received from workers to the appropriate PipelineSaver object.
    """

    name = "backend"

    def __init__(self, savers=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add queries for direct communication with pydra
        self.queries = {
            "messages": self.query_messages,
            "events": self.query_events,
            "data": self.query_data
        }
        # Recording events
        self.events["start_recording"] = self.start_recording
        self.events["stop_recording"] = self.stop_recording
        # Savers
        self.savers = savers
        self._threads = []

    def setup(self):
        """Start saver threads and send a connected message to pydra."""
        for cls_type, args, kwargs, connections in self.savers:
            new_cls = type(cls_type.name, (cls_type,), {"args": args, "kwargs": kwargs, "_connections": connections})
            thread = new_cls.start()
            self._threads.append(thread)
        self.connected()

    # @QCONNECTED
    # def connected(self):
    #     return ()

    @QUERY.callback
    def handle_query(self, qtype, **kwargs):
        print("HERE")
        print(qtype, kwargs)

    def _process(self):
        """Receive messages from workers."""
        self.poll()

    @EXIT
    def _exit(self):
        """Broadcasts an exit signal."""
        return ()

    def exit(self, *args, **kwargs):
        """Terminates the process loop."""
        # if self.recording:
        #     self.stop_recording()
        self._exit()
        for thread in self._threads:
            thread.join()
        super().exit()

    def start_recording(self, directory: str = None, filename: str = None, **kwargs):
        """Implements a start_recording event. Starts saving data."""
        print("START RECORDING")
        # if not self.recording:
        #     for pipeline in self.savers:
        #         pipeline.start(directory, filename)
        #     self.recording = True

    def stop_recording(self, **kwargs):
        """Implements a stop_recording event. Stops saving data."""
        print("STOP RECORDING")
        # if self.recording:
        #     for pipeline in self.savers:
        #         pipeline.stop()
        #     self.recording = False

    @QUERY.callback
    def handle_query(self, qtype, **kwargs):
        try:
            self.queries[qtype]()
        except KeyError:
            # TODO: SEND ERROR RATHER THAN RAISE ERROR
            raise ValueError(f"Saver -{self.name}- cannot respond to {qtype} queries from Pydra.")
        finally:
            return

    @QMESSAGES
    def query_messages(self, **kwargs):
        return

    @QEVENTS
    def query_events(self, **kwargs):
        return

    @QDATA
    def query_data(self, **kwargs):
        return
