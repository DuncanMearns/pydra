import zmq
from .messaging import *


class PydraObject:
    """Base class for pydra objects implementing zmq sockets for communicating between processes.

    Parameters
    ----------
    connections : dict
        Dictionary of all connections used in the pydra network. Each pydra object in the network should be represented
        in this dictionary with a unique key (the object's name), dictionary pair. The object's connection dictionary
        should have any number of the following keys and corresponding values:
            * publisher (str)
                The port on which the object publishes its outputs.
            * subscriptions (iterable)
                Elements should be a tuple of (name, port, message types). The name is the name of the worker to receive
                message from, the port is the port on which to subscribe to messages from this worker, and the message
                types are an iterable of ZMQMessage types to listen for.
            * sender (str)
                The port to which the object pushes messages with the PUSH|PULL pattern. Implemented by the Saver
                subclass for sending messages back to the main pydra class.
            * receiver (str)
                The port on which to receive messages from a PUSH|PULL pattern. Implemented by main pydra class for
                receiving messages from Saver.

    Attributes
    ----------
    msg_handlers : dict
        A dictionary that maps ZMQMessage types to appropriate handling methods.
    events : dict
        A dictionary that maps named events to corresponding methods. New worker-specific events can be added in
        subclasses.
    zmq_context : zmq.Context
        The zmq context object for implementing 0MQ functionality.
    zmq_connections : dict
        A copy of the object's specific connections from the dictionary provided by the connections parameters.
    zmq_publisher : zmq.Socket (only if "publisher" provided in connections)
        The zmq.PUB socket for publishing messages.
    zmq_subscriptions : dict of zmq.Socket (only if "subscriptions" provided in connections)
        A dictionary of zmq.SUB sockets for receiving messages from named workers in the network.
    zmq_poller : zmq.Poller (only if "subscriptions" provided in connections)
        Poller object for receiving messages from subscribed sockets.
    zmq_sender : zmq.Socket (only if "sender" provided in connections)
        The zmq.PUSH socket for sending messages.
    zmq_sender : zmq.Socket (only if "receiver" provided in connections)
        The zmq.PULL socket for receiving messages.

    Class Attributes
    ----------------
    name : str
        Unique name of the pydra object. Must be specified in subclasses.

    See Also
    --------
    pydra_zmq.core.pydra.Pydra
    pydra_zmq.core.saving.Saver
    pydra_zmq.core.workers.Worker
    pydra_zmq.core.process
    """

    name = ""

    def __init__(self, connections: dict, *args, **kwargs):
        super().__init__()
        # Get the zmq configuration
        self.zmq_connections = connections[self.name]
        # Create the zmq context and bindings
        self.zmq_context = zmq.Context.instance()
        # Set publisher
        if "publisher" in self.zmq_connections:
            port = self.zmq_connections["publisher"]
            self._zmq_set_publisher(port)
        # Listen to subscriptions
        if "subscriptions" in self.zmq_connections:
            args = self.zmq_connections["subscriptions"]
            self._zmq_set_subscriptions(*args)
        # Set sender
        if "sender" in self.zmq_connections:
            port = self.zmq_connections["sender"]
            self._zmq_set_sender(port)
        # Set receiver
        if "receiver" in self.zmq_connections:
            port = self.zmq_connections["receiver"]
            self._zmq_set_receiver(port)
        # Set message handlers
        self.msg_handlers = {
            "exit": self.exit,
            "message": self.handle_message,
            "event": self.handle_event,
            "data": self.handle_data,
            "trigger": self.send_trigger
        }
        # Create events
        self.events = {}
        # Wait for zmq connections
        time.sleep(1.0)

    def _zmq_set_publisher(self, port):
        """Creates the zmq_publisher for publishing messages."""
        self.zmq_publisher = self.zmq_context.socket(zmq.PUB)
        self.zmq_publisher.bind(port)

    def _zmq_set_subscriptions(self, *args):
        """Creates the zmq_subscriptions and poller for receiving messages."""
        # Create a poller to check for messages on subscription channels
        self.zmq_poller = zmq.Poller()
        # Connect to each subscription channel
        self.zmq_subscriptions = {}
        for (name, port, messages) in args:
            zmq_subscriber = self.zmq_context.socket(zmq.SUB)
            zmq_subscriber.connect(port)
            for message in messages:
                zmq_subscriber.setsockopt(zmq.SUBSCRIBE, message.flag)
            self.zmq_subscriptions[name] = zmq_subscriber
            self.zmq_poller.register(zmq_subscriber, zmq.POLLIN)

    def _zmq_set_sender(self, port):
        """Creates the zmq_sender for pushing messages to another pydra object."""
        self.zmq_sender = self.zmq_context.socket(zmq.PUSH)
        self.zmq_sender.connect(port)

    def _zmq_set_receiver(self, port):
        """Creates the zmq_receiver for receiving pushed messages."""
        self.zmq_receiver = self.zmq_context.socket(zmq.PULL)
        self.zmq_receiver.bind(port)

    def _destroy(self):
        """Destroys the 0MQ context."""
        self.zmq_context.destroy(200)

    def poll(self):
        """Checks for poller for new messages from all subscriptions and passes them to appropriate handlers."""
        sockets = dict(self.zmq_poller.poll(0))
        for name, sock in self.zmq_subscriptions.items():
            if sock in sockets:
                msg, source, timestamp, flags, args = PydraMessage.recv(sock)
                self.msg_handlers[msg](*args, msg=msg, source=source, timestamp=timestamp, flags=flags)

    def exit(self, *args, **kwargs):
        """Called when the EXIT message type is received. May be re-implemented in subclasses."""
        return

    @MESSAGE
    def send_message(self, s):
        """Sends a string to the zmq_publisher."""
        return s

    def handle_message(self, s, **kwargs):
        """Handles MESSAGE (i.e. string) messages received from other objects."""
        s = MESSAGE.decode(s)
        self.recv_message(s, **kwargs)

    def recv_message(self, s, **kwargs):
        """Method for handling strings received from other objects. May be re-implemented in subclasses.

        Parameters
        ----------
        s : str

        Other Parameters
        ----------------
        msg : str
            Message type flag.
        source : str
            Name of the source of the message.
        timestamp : float
            Time at which the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        print(f"{self.name} received from {kwargs.get('source', 'UNKNOWN')} at {kwargs.get('timestamp', 0.0)}:\n{s}")

    @TRIGGER
    def send_trigger(self, *args, **kwargs):
        """Simple method for implementing sending trigger messages."""
        return ()

    @EVENT
    def send_event(self, event_name, **kwargs):
        """Primary method for sending EVENT messages between pydra objects.

        Parameters
        ----------
        event_name : str
            The name of the event. Other pydra objects subscribing to events from this one will call the corresponding
            method in their events attribute.
        kwargs : dict
            Dictionary of keyword arguments associated with the event."""
        return event_name, kwargs

    def handle_event(self, event_name, event_kw, **kwargs):
        """Handles EVENT messages received from other objects."""
        event_name, event_kw = EVENT.decode(event_name, event_kw)
        if event_name in self.events:
            event_kw.update(**kwargs)
            self.events[event_name](**event_kw)

    @TIMESTAMPED
    def send_timestamped(self, t, data):
        """Sends timestamped data between objects.

        Parameters
        ----------
        t : float
            The timestamp associated with the data point.
        data : dict
            Dictionary of pickle-able data.
        """
        return t, data

    @INDEXED
    def send_indexed(self, t, i, data):
        """Sends indexed data between objects.

        Parameters
        ----------
        t : float
            A timestamp associated with the given index.
        i : int
            The index of the data.
        data : dict
            Dictionary of pickle-able data.
        """
        return t, i, data

    @FRAME
    def send_frame(self, t, i, frame):
        """Sends frama data between objects.

        Parameters
        ----------
        t : float
            The timestamp of the frame.
        i : int
            The index of the frame.
        frame : np.ndarray
            A numpy array containing data.
        """
        return t, i, frame

    def handle_data(self, *data, **kwargs):
        """Handles data messages (TIMESTAMPED, INDEXED, or FRAME) received from other objects."""
        flags = kwargs["flags"]
        if "t" in flags:
            self.recv_timestamped(*data, **kwargs)
        elif "i" in flags:
            self.recv_indexed(*data, **kwargs)
        elif "f" in flags:
            self.recv_frame(*data, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        """Method for handling serialized timestamped data received from other objects. May be re-implemented in
        subclasses.

        Parameters
        ----------
        t : bytes
            Byte representation of the timestamp (float) associated with the data.
        data : bytes
            Byte representation of the data (dictionary).

        Other Parameters
        ----------------
        msg : str
            Message type flag.
        source : str
            Name of the source of the message.
        timestamp : float
            Time at which the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        t, data = TIMESTAMPED.decode(t, data)
        return t, data

    def recv_indexed(self, t, i, data, **kwargs):
        """Method for handling serialized indexed data received from other objects. May be re-implemented in subclasses.

        Parameters
        ----------
        t : bytes
            Byte representation of the timestamp (float) associated with the data.
        i : bytes
            Byte representation of the of the index (int) associated with the data.
        data : bytes
            Byte representation of the data (dictionary).

        Other Parameters
        ----------------
        msg : str
            Message type flag.
        source : str
            Name of the source of the message.
        timestamp : float
            Time at which the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        t, i, data = INDEXED.decode(t, i, data)
        return t, i, data

    def recv_frame(self, t, i, frame, **kwargs):
        """Method for handling serialized frame data received from other objects. May be re-implemented in subclasses.

        Parameters
        ----------
        t : bytes
            Byte representation of the timestamp (float) associated with the data.
        i : bytes
            Byte representation of the of the index (int) associated with the data.
        frame : bytes
            Byte representation of the frame (np.ndarray).

        Other Parameters
        ----------------
        msg : str
            Message type flag.
        source : str
            Name of the source of the message.
        timestamp : float
            Time at which the message was sent.
        flags : str
            Additional flags received along with the message.
        """
        t, i, frame = FRAME.decode(t, i, frame)
        return t, i, frame
