from .handlers import *
from ..messaging import *
import traceback


__all__ = ("PydraType", "PydraObject", "PydraSender", "PydraReceiver", "PydraPublisher", "PydraSubscriber")


class PydraType(type):
    """Metaclass for Pydra objects ensures they have a name attribute."""

    def __new__(mcs, name, args, kw, **kwargs):
        if "name" not in kw:
            kw["name"] = name
        return super().__new__(mcs, name, args, kw, **kwargs)


class PydraObject(metaclass=PydraType):
    """Abstract base Pydra class. All Pydra objects in the network should be singletons with a unique class name."""

    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__()

    def exit(self, *args, **kwargs):
        """Called when the EXIT message type is received. May be re-implemented in subclasses."""
        return

    @ERROR
    def raise_error(self, error: Exception, message: str):
        return error, message


class PydraMessenger(PydraObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PydraListener(PydraObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.zmq_poller = ZMQPoller()
        # Set message handlers
        self.msg_callbacks = {
            "exit": self.exit
        }

    def poll(self, timeout=0):
        """Checks for poller for new messages from all subscriptions and passes them to appropriate handlers."""
        for msg, source, timestamp, flags, args in self.zmq_poller.poll(timeout):
            if msg in self.msg_callbacks:
                self.msg_callbacks[msg](*args, msg=msg, source=source, timestamp=timestamp, flags=flags)
                continue
            try:
                callback = "_".join(["handle", msg])
                self.__getattribute__(callback)(*args, msg=msg, source=source, timestamp=timestamp, flags=flags)
            except AttributeError:
                raise NotImplementedError(f"{self.name} has no method to handle '{msg}' messages.")
            except Exception as err:
                message = traceback.format_exc()
                self.raise_error(err, message)


class PydraSender(PydraMessenger):

    def __init__(self, sender=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if sender:
            self.zmq_sender = ZMQSender(sender)
        else:
            raise ValueError("sender not specified")

    @REQUEST.callback
    def handle_request(self, qtype, **kwargs):
        try:
            callback = "_".join(["reply", qtype])
            self.__getattribute__(callback)()
        except AttributeError:
            self.raise_error(ValueError(), f"Saver -{self.name}- cannot respond to {qtype} queries from Pydra.")
        finally:
            return

    @BACKEND.CONNECTION
    def reply_connection(self):
        raise NotImplementedError

    def reply_data(self):
        raise NotImplementedError

    @BACKEND.ERROR
    def raise_error(self, error: Exception, message: str):
        return error, message


class PydraReceiver(PydraListener):

    def __init__(self, receivers=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, port in receivers:
            self.add_receiver(name, port)

    def add_receiver(self, name, port):
        self.zmq_poller.add_receiver(name, port)


class PydraPublisher(PydraMessenger):

    def __init__(self, publisher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if publisher:
            self.zmq_publisher = ZMQPublisher(publisher)
        else:
            raise ValueError("publisher or port not specified")

    @STRING
    def send_string(self, s):
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

    @REQUEST
    def send_request(self, what: str):
        return what,


class PydraSubscriber(PydraListener):

    def __init__(self, subscriptions=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        for (name, port, messages) in subscriptions:
            self.add_subscription(name, port, messages)
        # Create dictionary for overwriting event callbacks
        self.event_callbacks = {}

    def add_subscription(self, name, port, messages):
        self.zmq_poller.add_subscription(name, port, messages)

    def _test_connection(self, **kwargs):
        """Called by the 'test_connection' event. Informs pydra that 0MQ connections have been established and worker is
        receiving messages."""
        self.connected()

    @CONNECTION
    def connected(self):
        return True,

    @CONNECTION
    def not_connected(self):
        return False,

    @STRING.callback
    def handle_string(self, s, **kwargs):
        """Handles MESSAGE (i.e. string) messages received from other objects."""
        self.recv_str(s, **kwargs)

    def recv_str(self, s, **kwargs):
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

    @TRIGGER.callback
    def handle_trigger(self, *args, **kwargs):
        self.recv_trigger(kwargs["source"], kwargs["timestamp"])

    def recv_trigger(self, source, t):
        return

    @EVENT.callback
    def handle_event(self, event_name, event_kw, **kwargs):
        """Handles EVENT messages received from other objects."""
        if event_name in self.event_callbacks:
            f = self.event_callbacks[event_name]
        else:
            try:
                f = self.__getattribute__(event_name)
            except AttributeError:
                return
        event_kw.update(**kwargs)
        f(**event_kw)

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
