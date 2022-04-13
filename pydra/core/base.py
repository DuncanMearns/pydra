from .messaging import *
import time


class PydraBase:

    name = ""

    def __init__(self, *args, **kwargs):
        # Wait for ZeroMQ connections
        time.sleep(1.0)

    def exit(self, *args, **kwargs):
        """Called when the EXIT message type is received. May be re-implemented in subclasses."""
        return


class PydraSender(PydraBase):

    def __init__(self, sender=None, *args, **kwargs):
        if sender:
            self.zmq_sender = ZMQSender(sender)
        else:
            raise ValueError("sender not specified")
        super().__init__(*args, **kwargs)


class PydraReceiver(PydraBase):

    def __init__(self, receiver=None, *args, **kwargs):
        if receiver:
            self.zmq_receiver = ZMQReceiver(receiver)
        else:
            raise ValueError("receiver not specified")
        super().__init__(*args, **kwargs)


class PydraPublisher(PydraBase):

    def __init__(self, publisher=None, port=None, *args, **kwargs):
        if publisher and port:
            self.zmq_publisher = ZMQPublisher(publisher)
            self.zmq_sub_port = port
        else:
            raise ValueError("publisher or port not specified")
        super().__init__(*args, **kwargs)

    @MESSAGE
    def send_message(self, s):
        """Sends a string to the zmq_publisher."""
        return s

    @TRIGGER
    def send_trigger(self):
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

        Other Parameters
        ----------------
            Keyword arguments associated with the event."""
        return event_name, kwargs

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

    @ARRAY
    def send_array(self, t, i, a):
        """Sends array data between objects.

        Parameters
        ----------
        t : float
            A timestamp associated with the given index.
        i : int
            The index of the data.
        a : np.ndarray
            A numpy array containing data.
        """
        return t, i, a

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


class PydraSubscriber(PydraBase):

    subscriptions = ()

    def __init__(self, subscriptions=(), *args, **kwargs):
        self.zmq_subscriber = SubscriptionManager(subscriptions)
        # Set message handlers
        self.msg_handlers = {
            "exit": self.exit,
            "message": self.handle_message,
            "event": self.handle_event,
            "data": self.handle_data,
            "trigger": self.handle_trigger
        }
        # Set event handlers
        self.events = {}
        super().__init__(*args, **kwargs)

    def poll(self):
        """Checks for poller for new messages from all subscriptions and passes them to appropriate handlers."""
        for flag, source, timestamp, other, args in self.zmq_subscriber.poll():
            self.msg_handlers[flag](*args, msg=flag, source=source, timestamp=timestamp, flags=other)

    def handle_message(self, s, **kwargs):
        """Handles MESSAGE (i.e. string) messages received from other objects."""
        s = MESSAGE.decode(s)[0]
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

    def handle_trigger(self, *args, **kwargs):
        self.recv_trigger(kwargs["source"], kwargs["timestamp"])

    def recv_trigger(self, source, t):
        pass

    def handle_event(self, event_name, event_kw, **kwargs):
        """Handles EVENT messages received from other objects."""
        event_name, event_kw = EVENT.decode(event_name, event_kw)
        if event_name in self.events:
            event_kw.update(**kwargs)
            self.events[event_name](**event_kw)

    def handle_data(self, *data, **kwargs):
        """Handles data messages (TIMESTAMPED, INDEXED, or FRAME) received from other objects."""
        flags = kwargs["flags"]
        if "t" in flags:
            data = TIMESTAMPED.decode(*data)
            self.recv_timestamped(*data, **kwargs)
        elif "i" in flags:
            data = INDEXED.decode(*data)
            self.recv_indexed(*data, **kwargs)
        elif "a" in flags:
            data = ARRAY.decode(*data)
            self.recv_array(*data, **kwargs)
        elif "f" in flags:
            data = FRAME.decode(*data)
            self.recv_frame(*data, **kwargs)

    def recv_timestamped(self, t, data, **kwargs):
        """Method for handling serialized timestamped data received from other objects. May be re-implemented in
        subclasses.

        Parameters
        ----------
        t : float
        data : dict

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
        pass

    def recv_indexed(self, t, i, data, **kwargs):
        """Method for handling serialized indexed data received from other objects. May be re-implemented in subclasses.

        Parameters
        ----------
        t : float
        i : int
        data : dict

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
        pass

    def recv_array(self, t, i, a, **kwargs):
        """Method for handling serialized array data received from other objects. May be re-implemented in subclasses.

        Parameters
        ----------
        t : float
        i : int
        a : np.ndarray

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
        pass

    def recv_frame(self, t, i, frame, **kwargs):
        """Method for handling serialized frame data received from other objects. May be re-implemented in subclasses.

        Parameters
        ----------
        t : float
        i : int
        frame : np.ndarray

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
        pass
