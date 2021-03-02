.. _using-pydra:

Using Pydra
===========

To learn the basics (and not-so-basics) of Pydra, you might want to start by working through the tutorial scripts. A
basic overview of how to use Pydra is provided below.

Importing and running Pydra
---------------------------

.. code-block:: python

    from pydra import Pydra, config, ports


    if __name__ == "__main__":

        # Automatically configure ZeroMQ connections
        Pydra.configure(config, ports)

        # Run the Pydra GUI with given configuration
        Pydra.run(**config)

This won't do anything other than start the Pydra GUI without any workers. To add workers to Pydra, you must create
*modules* and add them to the ``config``.

Creating your own workers
-------------------------

.. code-block:: python

    from pydra import Pydra, config, ports
    from pydra.core import Worker


    # Define a Worker class
    class MyWorker(Worker):

        name = "my_worker"  # give your worker a name
        subscriptions = ()  # if your worker needs to receive messages from others in the network, add the names of those
                            # workers to the subscriptions attribute here

        def __init__(self, *args, **kwargs):
            # You always need to put this at the beginning of a Worker's __init__
            super().__init__(*args, **kwargs)

            # Put your constructor code here
            # ...

            # Define events for your worker to respond to
            self.events["my_event"] = self.my_event

        def my_event(self, **kwargs):
            """Code here will be called whenever receives an event called "my_event"."""
            # Use send_frame(...) to broadcast frame data through the pydra network
            # Use send_indexed(...) to broadcast indexed data through the pydra network
            # Use send_timestamped(...) to broadcast timestamped data through the pydra network
            pass

        def recv_frame(self, t, i, frame, **kwargs):
            """Put code here to do something with frame data received through the pydra network"""
            return

        def recv_indexed(self, t, i, frame, **kwargs):
            """Put code here to do something with indexed data received through the pydra network"""
            return

        def recv_timestamped(self, t, data, **kwargs):
            """Put code here to do something with timestamped data received through the pydra network"""
            return


    # Create a module with your worker
    MY_MODULE = {
        "worker": MyWorker
    }


    # Add your module to the configuration
    config["modules"] = [MY_MODULE]
    # OR
    # config["modules"].append(MY_MODULE)


    if __name__ == "__main__":

        # Automatically configure ZeroMQ connections
        Pydra.configure(config, ports)

        # Run the Pydra GUI with given configuration, which now includes your worker
        Pydra.run(**config)

For debugging your workers, it is sometimes useful to run Pydra without the GUI. You can do this by instantiating a
Pydra object directly in your main code.

.. code-block:: python

    from pydra import Pydra, config, ports


    # Define workers and modules here
    # ...


    if __name__ == "__main__":

        # Automatically configure ZeroMQ connections
        Pydra.configure(config, ports)

        # Create an instance of a Pydra object
        pydra = Pydra(**config)

        # Put some test code here
        # ...

        # Make sure Pydra exits correctly (ZeroMQ connections and processes are properly closed/terminated)
        pydra.exit()

Adding widgets to the Pydra GUI
-------------------------------
To add your own widgets to the Pydra GUI, make a subclass of :obj:`ModuleWidget` and add it to your worker's module.

.. code-block:: python

    from pydra import Pydra, config, ports
    from pydra.core import Worker
    from pydra.gui import ModuleWidget


    # Define a Worker class
    class MyWorker(Worker):

        name = "my_worker"  # give your worker a name

        # Worker __init__ and other methods here
        # ...


    # Create a widget for your worker
    class MyWidget(ModuleWidget):

        # Define Qt signals here
        # ...

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Your __init__ code here
            # ...

        # Qt slots and other methods here

        def my_method(self):
            """Connect this method to a Qt signal in __init__."""
            # Use the send_event method to communicate with your worker in the pydra network
            self.send_event("my_event")


    # Create a module with your worker and widget
    MY_MODULE = {
        "worker": MyWorker,
        "widget": MyWidget  # add a widget to the module
    }


    # Add your module to the configuration
    config["modules"] = [MY_MODULE]
    # OR
    # config["modules"].append(MY_MODULE)


    if __name__ == "__main__":

        # Automatically configure ZeroMQ connections
        Pydra.configure(config, ports)

        # Run the Pydra GUI with given configuration, which now includes your worker and an associated widget
        Pydra.run(**config)

