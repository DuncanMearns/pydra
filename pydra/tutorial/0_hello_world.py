"""
# Hello world example for Pydra.
#
# In this example, we create a Pydra Worker class called HelloWorld. When we run Pydra, this worker will be migrated to
# a separate process and start receiving events. Whenever an event is received, our worker will check whether it can
# respond to the event and then call a corresponding method. In this example, our worker has a single event called
# "hello_world" which calls the method hello_world.
#
# To use our worker class, we must create a module. Modules are dictionaries, and to include our worker, we must assign
# it to the "worker" key. Note, that this should be the class itself, and not an instance. Modules are added to the config
# dictionary used to initialize Pydra.
#
# Since Pydra runs a 0MQ network, connections between ports must be configured. This is done under the hood when we  call
# Pydra's configure method. This method additionally takes a list of ports that Pydra should use to configure the 0MQ
# network. Most applications of Pydra will first involve configuring the network.
# >>> from pydra import Pydra, config, ports
# >>> Pydra.configure(config, ports)
#
# To start using Pydra, we create an instance of the Pydra class. The config dictionary is unpacked by Pydra's constructor
# and should be passed using the **kwargs pattern. The Pydra class should only be substantiated once. Instantiating the
# Pydra class will migrate workers to new processes and setup the 0MQ network.
# >>> pydra = Pydra(**config)
#
# Once Pydra is configuring and an instance has been instantiated, we can start sending events to the workers we created
# and passed to Pydra in our modules. Calling Pydra's send_event method will allow us to broadcast events to our workers.
# >>> pydra.send_event("hello_world")
#
# After we are finished sending events to our workers, we should make sure that all our processes rejoin the main process
# and 0MQ connections are properly closed. Calling Pydra's exit method ensures a clean exit.
# >>> pydra.exit()
"""
from pydra import Pydra, config, ports
from pydra.core.main.workers import Worker
import time


class HelloWorld(Worker):
    """Worker class"""

    # Every pydra worker must have a unique name
    name = "hello_world"

    def __init__(self, *args, **kwargs):
        # The worker's constructor is only called after it has been migrated to a new process
        # Call to super() within the constructor is needed to initialize connections in the network
        super().__init__(*args, **kwargs)
        # Add an event called "hello_world" to the worker and map it to a corresponding method
        self.events["hello_world"] = self.hello_world

    def hello_world(self, **kwargs):  # keyword arguments are passed from the event handler
        """Method called when pydra sends the 'hello_world' event."""
        print("hello, world!")


# Create a module for our HelloWorld worker
HELLOWORLD = {
    "worker": HelloWorld
}


# Add the HELLOWORLD module to pydra's configuration dictionary
config["modules"] = [HELLOWORLD]


if __name__ == "__main__":

    # Configure 0MQ connections
    Pydra.configure(config, ports)

    # Create the pydra object
    print("CREATING THE PYDRA OBJECT")
    pydra = Pydra(**config)

    # Send an event called "hello_world" to the network
    print("\nSENDING HELLO_WORLD EVENT")
    pydra.send_event("hello_world")

    # Sleep for one second
    time.sleep(1.0)

    # Send an event called "goodbye_world" to the network
    # This will be ignored unless one of our workers implements such an event
    print("\nSENDING GOODBYE_WORLD EVENT")
    pydra.send_event("goodbye_world")

    # Sleep for one second
    time.sleep(1.0)

    # Exit (should be called for clean exiting of processes)
    print("\nSENDING EXIT SIGNAL\n")
    pydra.exit()
