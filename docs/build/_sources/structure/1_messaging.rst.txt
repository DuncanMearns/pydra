Messaging in Pydra
==================

At the heart of Pydra's functionality are the :class:`~pydra.core.base.PydraObject` and
:class:`~pydra.core.messaging.PydraMessage` classes. Pydra objects handle messaging between processes using ZeroMQ sockets.
Pydra messages provide a means for messages to be sent between, and interpreted by, Pydra objects.

A note on ZeroMQ
----------------

The Pydra network and messaging functionality is provided through the ZeroMQ library. ZeroMQ is a very general library
that allows messages to be passed over network ports (typically TCP). A comprehensive guide can be found
`here <https://zguide.zeromq.org/>`_.

ZeroMQ provides two major advantages:

1. Since it is network-based, it can send messages between computers.
2. It is available in multiple programming languages (including Java - which, by extension, means it can be used with
   MATLAB).

Nodes in a ZeroMQ network are connected via pairs of "sockets" that bind to ports. ZeroMQ provides numerous patterns
by which messages can be sent between sockets. Pydra predominantly makes use of two of these patterns:

* PUB-SUB: this is a one-to-many pattern, allowing one node to send messages to many others.
* PUSH-PULL: this is a one-to-one unidirectional pattern, allowing one node to push messages to another.

While Pydra handles all ZeroMQ messaging under-the-hood (including serialization and deserialization of messages), a
basic understanding of the library is helpful when it comes to understanding the guts of Pydra - especially if you want
to create custom message types and/or use Pydra to communicate with other programming languages.

In addition, it is helpful to understand that objects in Pydra predominately communicate over network ports (rather than
pipes or queues). The downside is that these ports and subscriptions must be properly configured - which can be a little
finicky. For simple networks running on a single computer, Pydra can configure everything automatically. However, for
more complex network architectures involving multiple computers or triggers, manual configuration of the ZeroMQ network is
necessary.

PydraObject
-----------

There are three Pydra object classes:

* The main :class:`~pydra.pydra.Pydra` class
* The :class:`~pydra.core.saving.Saver` class
* The :class:`~pydra.core.workers.Worker` class

Pydra objects are initialized with a dictionary of connections. These connections link different Pydra objects within
the network to specific ports. Depending on the subclass, Pydra objects may have any combination of PUB-SUB sockets and
PUSH-PULL sockets.

PydraMessage
------------

Pydra objects communicate with each other via Pydra messages. Pydra messages provide a means to send various data types
over ZeroMQ sockets. First and foremost, the :class:`~pydra.core.messaging.PydraMessage` class provides a means to
generate decorators that alter the behavior of Pydra object methods - allowing them to publish their outputs to their
respective ZeroMQ sockets. Moreover, Pydra messages have :meth:`~pydra.core.messaging.PydraMessage.encode` and
:meth:`~pydra.core.messaging.PydraMessage.decode` methods that allow specific data types to be serialized and
deserialized. Finally, Pydra messages prepend various tags to data sent over sockets, providing target objects with all
the necessary information needed to decode and handle messages at the other end.

Each type of :class:`~pydra.core.messaging.PydraMessage` has a unique flag associated with it. This flag allows
receiving objects to pass the message to the correct handler. Each message type also encodes / decodes specific
combinations of data types that serve specific functions within the Pydra network. The main message types are:

========  =========================  ===========================================
Flag      Data                       Function
========  =========================  ===========================================
EXIT      None                       Provides a top-level exit signal
MESSAGE   str                        Pass strings between Pydra objects
EVENT     (str, dict)                Call methods of other Pydra objects
DATA      {float, int, dict, array}  Pass data between Pydra objects (see below)
========  =========================  ===========================================


Other message types - such as LOGGED and INFO - serve more specialized functions in communications between
specific kinds of Pydra object.

Pydra objects can pass data to each other via DATA messages. There are three data formats that Pydra can handle. These
are:

===========  =======  ===================  =========================================================
Name         Flags    Signature            Description
===========  =======  ===================  =========================================================
FRAME        DATA, f  (float, int, array)  A timestamped, indexed numpy array (e.g. video frame)
INDEXED      DATA, i  (float, int, dict)   Timestamped, indexed data (e.g. tracking coordinate data)
TIMESTAMPED  DATA, t  (float, dict)        Timestamped data not associated with any particular index
===========  =======  ===================  =========================================================
