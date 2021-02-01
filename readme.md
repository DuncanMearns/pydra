Pydra is a library for building control systems for experimental setups. It allows users to build networks of _workers_
that communicate with each other via messages over [ZeroMQ](https://zeromq.org/). It is designed with simplicity,
flexibility and modularity in mind (although it might not always deliver on any or all those fronts...).

Pydra also provides a Graphical User Interface built with PyQt.

_Pydra_ is a portmanteau of Python and hydra.


# ZeroMQ

---

The Pydra network and messaging functionality is provided through the ZeroMQ library. ZeroMQ is a very general library
that allows messages to be passed over network ports (typically TCP). A comprehensive guide can be found 
[here](https://zguide.zeromq.org/).

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
more complex network architectures involving multiple computers or triggers, manual configuration of the 0MQ network is
necessary.

# Messaging in Pydra

---

At the heart of Pydra's functionality are the
[`PydraObject`](pydra/core/base.py) and 
[`PydraMessage`](pydra/core/messaging/__init__.py)
classes. Pydra objects handle messaging between processes using 0MQ sockets. Pydra messages provide a means for messages
to be sent between, and interpreted by, Pydra objects. 

### PydraObject

There are three Pydra object classes:
* The main [`Pydra`](#pydra) class
* The [`Saver`](#saver) class
* The [`Worker`](#worker) class

Pydra objects are initialized with a dictionary of connections. These connections link different Pydra objects within
the network to specific ports. Depending on the subclass, Pydra objects may have any combination of PUB-SUB sockets and 
PUSH-PULL sockets.

### PydraMessage

Pydra objects communicate with each other via Pydra messages. Pydra messages provide a means to send various data types
over 0MQ sockets. First and foremost, the PydraMessage class provides a means to generate decorators that alter the
behavior of Pydra object methods - allowing them to publish their outputs to their respective 0MQ sockets. Moreover,
Pydra messages have `encode` and `decode` methods that allow specific data types to be serialized and deserialized. 
Finally, Pydra messages prepend various tags to data sent over sockets, providing target objects with all the necessary
information needed to decode and handle messages at the other end.

Each type of PydraMessage has a unique flag associated with it. This flag allows receiving objects to pass the message
to the correct handler. Each message type also encodes / decodes specific combinations of data types that serve specific
functions within the Pydra network. The main message types are:

| Flag      | Data types                | Function                                      |
| --------- |:------------------------- |:--------------------------------------------- |
| EXIT      | None                      | Provides a top-level exit signal              | 
| MESSAGE   | str                       | Pass strings between Pydra objects            |
| EVENT     | (str, dict)               | Call methods of other Pydra objects           |
| DATA      | {float, int, dict, array} | Pass data between Pydra objects (see below)   |

Other message types - such as `LOGGED` and `INFO` - serve more specialized functions in communications between
specific kinds of Pydra object.

Pydra objects can pass data to other via `DATA` messages. There are three data formats that Pydra can handle. These
are:

| Name          | Flags     | Signature             | Description                                               |
| ------------- |:--------- |:--------------------- |:--------------------------------------------------------- |
| FRAME         | DATA, f   | (float, int, array)   | A timestamped, indexed numpy array (e.g. video frame)     |
| INDEXED       | DATA, i   | (float, int, dict)    | Timestamped, indexed data (e.g. tracking coordinate data) |
| TIMESTAMPED   | DATA, t   | (float, dict)         | Timestamped data not associated with any particular index |


# Structure of Pydra

---

Pydra is, in essence, a network of processes connected over 0MQ. Each process contains a Pydra object and runs an event
loop. Each network contains a single instance of the main [`Pydra`](#pydra-class) class and a single instance of the
[`Saver`](#saver-class) class. In addition, the network may contain any number of [`Worker`](#worker-class) instances.

`Pydra` has access to all other processes in the network. `Pydra` broadcasts `EVENT` messages to all other processes,
as well as providing the `EXIT` signal. This broadcast is achieved via a PUB-SUB pattern over a port that all other
processes subscribe to. In addition, `Pydra` pulls messages (PUSH-PULL pattern) from a direct line to the `Saver`. This
channel is protected for communication exclusively between `Pydra` and `Saver`. `Workers` receive messages from `Pydra`
as well as from other `Workers`. Each `Worker` has a port to which it publishes all its messages. These messages are
effectively spewed into the void, where they can be picked up by other `Workers`. All messages from `Workers` are picked
up by the `Saver`, which chooses to either ignore them, do something with them (such as saving data), or forward them to
`Pydra`.

Thus, the Pydra network forms a loop:  
`Pydra` -> `Worker` & `Saver`  
`Worker` -> `Saver`  
`Saver` -> `Pydra`

Within the network of `Workers`, connections can be as simple or complicated as required, providing maximum flexibility.

### Processes in Pydra

The main `Pydra` object is typically instantiated in the main process. The `Worker` and `Saver` instances, however, each
run in their own processes. This is achieved via the 
[`ProcessMixIn`](pydra/core/process.py) and 
[`PydraProcess`](pydra/core/process.py) classes.
A `PydraProcess` runs an event loop within a process. The process contains a single instance of either a `Worker` or a 
`Saver` object. As the event loop runs, all ports that the object subscribes to are continuously checked for new 
messages. Once a message is received, it is passed to the appropriate handler. Handler methods _must_ return (ideally 
quickly) so that ports can be checked for new messages. The event loop only ends, and the process terminates, once the
`EXIT` signal has been received from `Pydra`.

If a `Worker` gets stuck in an endless loop (or crashes), it can become inaccessible even after all other processes have
exited. If this happens, 0MQ sockets might still be open, preventing them from being reused and causing crashes when the
program is restarted.


# PydraObjects

---
This section provides more details about each type of PydraObject.

## Worker

The [`Worker`](pydra/core/workers.py) is the main class that users need to worry about and work with. The base class 
provides the bare minimum required to function within the Pydra network. More specific use cases are also provided by 
Pydra.

###### Class attributes
`name`: Each worker within the Pydra network **must** have a *unique* name. Even if two workers are running the exact 
same code, they must be uniquely named. This is because Pydra provides a unique 0MQ port to each worker in the network 
for publishing its messages. Furthermore, connections between workers are established using their names.

`subscriptions`: Every worker automatically receives `EXIT` and `EVENT` messages from Pydra. In addition, they receive 
`EVENT` and `DATA` messages from all the workers whose names appear in their subscriptions.  

`pipeline`: For more advanced network architectures, workers may be assigned to a specific [pipeline](#pipelines).  

`plot`: Any data that workers publish to their 0MQ port and listed in their plot attribute will be plotted in the GUI.

###### Events
Every worker contains an `event` attribute, which is a dictionary specified in the constructor. The event dictionary
maps strings to methods. When an `EVENT` message is received, the event handler checks whether the event name appears
in the worker's event dictionary. If it does, then that method is called along with keyword arguments delivered with
the `EVENT` message. These keyword arguments will also contain the message tags associated with the `EVENT`. These tags
include the _"source"_ of the `EVENT`, in case users want to have different functionality for the same `EVENT` received
from different workers.

`Pydra` has a some special, protected events that it sends to all workers which are necessary for initializing the
network and establishing communication with the `Saver`. Therefore, new events should _always_ be added to the `events`
dictionary by updating the pre-existing attribute, rather than by overwriting it.

`Pydra` sends out a few events that may optionally be added to a worker's `events` dictionary, but are not included by
default. These include _"start_recording"_ and _"stop_recording"_, as well as events for changing working directories
and file names.

###### The event loop
Pydra workers run in processes that are separate from the main process. Therefore, they are not instantiated until they
have been migrated to their own process. After the `Worker` object is created (by calling its constructor, along with
parameters passed from `Pydra`), its `run` method is immediately called. The `run` method does three things:

1. First, the worker's `setup` method is called once.
   
2. Next, the worker enters its event loop. While the event loop is running, it constantly calls the `_process` method.
   In the base `Worker` class, this polls the worker's sockets for new messages. Polling receives and handles all 
   messages that have arrived since the last pass of the event loop. If no messages have been received, it will return
   immediately without blocking. Therefore, overrides of the `_process` method must always include a call to super().
   
3. Finally, after the `EXIT` signal has been received from `Pydra`, the event loop terminates, and the worker calls its 
   `cleanup` method. After cleanup, the process will join the main process.
   
The `setup`, `_process` and `cleanup` methods can all be overridden in subclasses of `Worker`, with the caveats 
mentioned above.
   
###### Sending and receiving messages
Workers can communicate with other workers, with the `Saver`, and with `Pydra` (via the `Saver`). Whilst custom message
types can be created and sent using decorators, for convenience the base `PydraObject` class provides a simple means of
broadcasting common message types. Broadcast messages are received by other "subscribed" workers, and by the `Saver`.

`EVENT` messages can be sent with the `send_event` method. This takes a string (the event name) and optional keyword
arguments that will be passed to receiver's corresponding method.

`DATA` messages can be sent with one of three methods:

* `send_frame` can be used to send `FRAME` type data messages, consisting of timestamped and indexed numpy arrays.

* `send_indexed` can be used to send `INDEXED` type data messages, consisting of a timestamp and index, as well as a 
  dictionary of named data values.
    
* `send_timestamped` can be used to send `TIMESTAMPED` type data messages. Timestamped messages are similar to indexed 
  messages, consisting of a dictionary of named data values. However, timestamped data do not have any index associated
  with them.
  
Just as workers can send `DATA` messages using the methods highlighted above, they can also receive data. The 
corresponding methods for handling received data are:
* `recv_frame` for `FRAME` type data.
* `recv_indexed` for `INDEXED` type data.
* `recv_timestamped` for `TIMESTAMPED` type data.

Note that these methods are called for any and all data received from workers in the `subscriptions`. If workers will be 
receiving the same data type from multiple sources in the network - and those data need to be handled separately - the 
_"source"_ of every message is included within the keyword arguments passed to every `recv_` method.

If the functionality of a `Worker` is significantly affected by whom it receives messages from, consider distributing 
the tasks among multiple separate workers, provided the processing power of the computer allows it (remember - every
worker runs in its own process!). Workers can be assigned to [pipelines](#pipelines) to ensure that like data are saved
together.

Finally, messages that are destined for the main `Pydra` object need to be decorated with the `LOGGED` message type. 
Note, however, that `DATA` from all workers are _automatically_ forwarded to `Pydra` by the `Saver`.

## Pydra

## Saver

# Pydra GUI

# Modules

# Pipelines
