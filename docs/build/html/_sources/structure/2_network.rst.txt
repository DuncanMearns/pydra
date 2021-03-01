Pydra network
=============

Pydra is, in essence, a network of processes connected over ZeroMQ. Each process contains a
:class:`~pydra.core.base.PydraObject` and runs an event loop. Each network contains a single instance of the main
:class:`~pydra.pydra.Pydra` class and a single instance of the :class:`~pydra.core.saving.Saver` class. In addition,
the network may contain any number of :class:`~pydra.core.workers.Worker` instances.

:class:`~pydra.pydra.Pydra` has access to all other processes in the network. :class:`~pydra.pydra.Pydra` broadcasts
EVENT messages to all other processes, as well as providing the EXIT signal. This broadcast is achieved via a *PUB-SUB*
pattern over a port that all other processes subscribe to. In addition, :class:`~pydra.pydra.Pydra` pulls messages
(*PUSH-PULL* pattern) from a direct line to the :class:`~pydra.core.saving.Saver`. This channel is protected for
communication exclusively between :class:`~pydra.pydra.Pydra` and :class:`~pydra.core.saving.Saver`. 
:class:`~pydra.core.workers.Worker` objects receive messages from :class:`~pydra.pydra.Pydra` as well as from other
:class:`~pydra.core.workers.Worker` objects. Each :class:`~pydra.core.workers.Worker` has a port to which it publishes
all its messages. These messages are effectively spewed into the void, where they can be picked up by other
:class:`~pydra.core.workers.Worker` objects. All messages from :class:`~pydra.core.workers.Worker` objects are picked up
by the :class:`~pydra.core.saving.Saver`, which chooses to either ignore them, do something with them (such as saving
data), or forward them to :class:`~pydra.pydra.Pydra`.

Thus, the Pydra network forms a loop:

* :class:`~pydra.pydra.Pydra` -> :class:`~pydra.core.workers.Worker` & :class:`~pydra.core.saving.Saver`
* :class:`~pydra.core.workers.Worker` -> :class:`~pydra.core.saving.Saver`
* :class:`~pydra.core.saving.Saver` -> :class:`~pydra.pydra.Pydra`

Within the network of :class:`~pydra.core.workers.Worker` objects, connections can be as simple or complicated as
required, providing maximum flexibility.

PydraObjects and their inputs / outputs:
.. image:: ../_static/pydra_cheatsheet.png


Processes in Pydra
------------------

The main :class:`~pydra.pydra.Pydra` object is typically instantiated in the main process.
The :class:`~pydra.core.workers.Worker` and :class:`~pydra.core.saving.Saver` instances, however, each run in their own
processes. This is achieved via the :class:`~pydra.core.process.ProcessMixIn` and
:class:`~pydra.core.process.PydraProcess` classes. A :class:`~pydra.core.process.PydraProcess` runs an event loop within
a process. The process contains a single instance of either a :class:`~pydra.core.workers.Worker` or a
:class:`~pydra.core.saving.Saver` object. As the event loop runs, all ports that the object subscribes to are continuously
checked for new messages. Once a message is received, it is passed to the appropriate handler. Handler methods *must*
return (ideally quickly) so that ports can be checked for new messages. The event loop only ends, and the process
terminates, once the EXIT signal has been received from :class:`~pydra.pydra.Pydra`.

If a :class:`~pydra.core.workers.Worker` gets stuck in an endless loop (or crashes), it can become inaccessible even
after all other processes have exited. If this happens, ZeroMQ sockets might still be open, preventing them from being
reused and causing crashes when the program is restarted.
