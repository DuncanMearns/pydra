PydraObjects
============

This section provides more details about each type of :class:`~pydra.core.base.PydraObject`.

Worker
------

The :class:`~pydra.core.workers.Worker` is the main class that users need to worry about and work with. The base class
provides the bare minimum required to function within the Pydra network. More specific use cases are also provided by
Pydra.

**Class attributes**

:obj:`name`: Each worker within the Pydra network **must** have a *unique* name. Even if
two workers are running the exact same code, they must be uniquely named. This is because Pydra provides a unique ZeroMQ
port to each worker in the network for publishing its messages. Furthermore, connections between workers are established
using their names.

:obj:`subscriptions`: Every worker automatically receives EXIT and EVENT messages
from :class:`~pydra.pydra.Pydra`. In addition, they receive EVENT and DATA messages from all the workers whose names
appear in their subscriptions.

:obj:`pipeline`: For more advanced network architectures, workers may be assigned to a
specific pipeline.

**Events**

Every worker contains an :obj:`events` attribute, which is a dictionary specified in the constructor. The event
dictionary maps strings to methods. When an EVENT message is received, the event handler checks whether the event name
appears in the worker's event dictionary. If it does, then that method is called along with keyword arguments delivered
with the EVENT message. These keyword arguments will also contain the message tags associated with the EVENT. These tags
include the *"source"* of the EVENT, in case users want to have different functionality for the same EVENT received from
different workers.

:class:`~pydra.pydra.Pydra` has a some special, protected events that it sends to all workers which are necessary for
initializing the network and establishing communication with the :class:`~pydra.core.saving.Saver`. Therefore, new
events should *always* be added to the :obj:`events` dictionary by updating the pre-existing attribute, rather than by
overwriting it.

:class:`~pydra.pydra.Pydra` sends out a few events that may optionally be added to a worker's `events` dictionary, but
are not included by default. These include *"start_recording"* and *"stop_recording"*, as well as events for changing
working directories and file names.

**The event loop**

Pydra workers run in processes that are separate from the main process. Therefore, they are not instantiated until they
have been migrated to their own process. After the :class:`~pydra.core.workers.Worker` object is created (by calling its
constructor, along with parameters passed from :class:`~pydra.pydra.Pydra`), its
:meth:`~pydra.core.process.ProcessMixIn.run` method is immediately called. The :obj:`run` method does three things:

1. First, the worker's :meth:`~pydra.core.process.ProcessMixIn.setup` method is called once.
2. Next, the worker enters its event loop. While the event loop is running, it constantly calls the
:meth:`~pydra.core.process.ProcessMixIn._process` method. In the base `Worker` class, this polls the worker's sockets
for new messages. Polling receives and handles all messages that have arrived since the last pass of the event loop. If
no messages have been received, it will return immediately without blocking. Therefore, overrides of the
:meth:`~pydra.core.process.ProcessMixIn._process` method must always include a call to :obj:`super()`.
3. Finally, after the EXIT signal has been received from :class:`~pydra.pydra.Pydra`, the event loop terminates, and the
worker calls its :meth:`~pydra.core.process.ProcessMixIn.cleanup` method. After cleanup, the process is free to join
the main process.

The :obj:`setup()`, :obj:`_process()` and :obj:`cleanup()` methods can all be overridden in subclasses of :obj:`Worker`,
with the caveats mentioned above.

**Sending and receiving messages**

Workers can communicate with other workers, with the :class:`~pydra.core.saving.Saver`, and with
:class:`~pydra.pydra.Pydra` (via the :class:`~pydra.core.saving.Saver`). Whilst custom message types can be created and
sent using decorators, for convenience the base :class:`~pydra.core.base.PydraObject` class provides a simple means of
broadcasting common message types. Broadcast messages are received by other "subscribed" workers, and by the
:class:`~pydra.core.saving.Saver`.

EVENT messages can be sent with the :method:`~pydra.core.base.PydraObject.send_event` method. This takes a string
(the event name) and optional keyword arguments that will be passed to the receiver's corresponding method.

DATA messages can be sent with one of three methods:

* :meth:`~pydra.core.base.PydraObject.send_frame` can be used to send FRAME type data messages, consisting of
timestamped and indexed numpy arrays.

* :meth:`~pydra.core.base.PydraObject.send_indexed` can be used to send INDEXED type data messages, consisting of a
timestamp and index, as well as a dictionary of named data values.

* :meth:`~pydra.core.base.PydraObject.send_timestamped` can be used to send TIMESTAMPED type data messages. Timestamped
messages are similar to indexed messages, consisting of a dictionary of named data values. However, timestamped data do
not have any index associated with them.

Just as workers can send DATA messages using the methods highlighted above, they can also receive data. The
corresponding methods for handling received data are:

* :meth:`~pydra.core.base.PydraObject.recv_frame` for FRAME type data.
* :meth:`~pydra.core.base.PydraObject.recv_indexed` for INDEXED type data.
* :meth:`~pydra.core.base.PydraObject.recv_timestamped` for TIMESTAMPED type data.

Note that these methods are called for any and all data received from workers in the :obj:`subscriptions`. If workers
will be receiving the same data type from multiple sources in the network - and those data need to be handled separately
- the *"source"* of every message is included within the keyword arguments passed to every :obj:`recv_` method.

If the functionality of a :class:`~pydra.core.workers.Worker` is significantly affected by whom it receives messages
from, consider distributing the tasks among multiple separate workers, provided the processing power of the computer
allows it (remember - every worker runs in its own process). Workers can be assigned to pipelines to ensure that like
data are saved together.

Finally, messages that are destined for the main :class:`~pydra.pydra.Pydra` object need to be decorated with the LOGGED
message type. Note, however, that DATA from all workers are *automatically* forwarded to :class:`~pydra.pydra.Pydra` by
the :class:`~pydra.core.saving.Saver`.

Pydra
-----

Saver
-----
