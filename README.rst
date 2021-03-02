Pydra - experiment control
==========================

Pydra is a library for building control systems for experimental setups. It allows users to build networks of *workers*
that communicate with each other via *messages* over `ZeroMQ <https://zeromq.org/>`_. It is designed with simplicity,
flexibility and modularity in mind (although it might not always deliver on any or all those fronts...). Pydra also
has a Graphical User Interface (GUI) built with PyQt.

**Pydra** is a portmanteau of Python and hydra.

For questions about this code, contact Duncan Mearns: mearns@neuro.mpg.de


Contents:

1. `Installation`_
2. `Using Pydra`_

Read the complete user guide `here <https://duncanmearns.github.io/pydra/>`_.

.. _installation:

Installation
============

Clone or fork the github repository
-----------------------------------

Download Pydra by cloning the repository (to download a static version of the code to your computer) or forking the
repository to create a copy in your own github account. You should then be able to open Pydra as a project in the IDE
of your choice. I like to use `PyCharm <https://www.jetbrains.com/pycharm/download/#section=windows>`_ community
edition, which is a free and powerful IDE, but does have quite a steep learning curve.

Install the pydra environment
-----------------------------

Pydra has an environment.yml file that should allow you to create a Python "environment" in which you can run Pydra
code. To create the environment, first make sure that you have
`Anaconda <https://www.anaconda.com/products/individual>`_ installed on your computer.  Help for managing environments
in Anaconda can be found
`here <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ . I recommend keeping
note of the directory where you install Anaconda, since you might have to navigate back to this in the future.

To create an environment for running Pydra, open a terminal window, such as Anaconda prompt. Next navigate to the Pydra
repository. If you are using Windows you can navigate through directories using the ``cd`` command.

.. code-block::

    # To navigate to a higher directory type:
    cd ..
    # To navigate to a lower directory type:
    cd <FOLDER>


Once you are in the pydra directory, you can create an Anaconda environment by typing:

.. code-block::

    conda env create -f environment.yml


It is also possible to create the environment file without navigating to the pydra directory by typing:

.. code-block::

    conda env create -f <PATH>


Where <PATH> is the complete path to the environment.yml file in the pydra repository.

To check that the environment is properly installed, you can check your Anaconda environments by typing:

.. code-block::

    conda env list


The pydra environment should be listed there as ``pydra_env``.


Install opencv
--------------

For Pydra to work correctly, you need to install opencv. To do this, first you must activate the pydra environment by
typing:

.. code-block::

    conda activate pydra_env


Next, install opencv by typing:

.. code-block::

    pip install opencv-python


Add Pydra to the environment
----------------------------

If you want to use Pydra without modifying the source code, you can add it to the ``pydra_env`` to be used in other
projects. To do this, make sure your ``pydra_env`` is activated then type:

.. code-block::

    pip install <PATH>


Where <PATH> is the path to your local copy of pydra (i.e. whichever folder contains the setup.py file).

To install Pydra directly from Github, see answers to
`this <https://stackoverflow.com/questions/20101834/pip-install-from-git-repo-branch>`_ question on stackoverflow.


Install additional libraries
----------------------------

To install other libraries in Pydra, make sure the environment is activated and then use:

.. code-block::

    pip install <LIBRARY>
    # or
    conda install <LIBRARY>


Configuring your IDE for Pydra
------------------------------

To start using Pydra, you will need to set the IDE interpreter for your pydra project to the environment you just
installed. If you are using PyCharm, you can do this by going to
``File > Settings... > Project: pydra > Python Interpreter``.

Next, click the cog in the top right and click ``Add...``.

Next select ``Conda Environment`` from the panel on the left, and then select ``Existing environment`` on the right.

Click ``...`` next to the ``Interpreter`` dropdown and navigate to the ``python.exe`` file in your
``pydra_env`` folder. This will be in the ``envs`` folder of your Anaconda installation (which you should have kept
note of from before). If you cannot find the ``pydra_env`` in the ``envs`` folder of your base Anaconda
installation, check the ``.conda`` directory in your account if you are using Windows (located in
``C:/Users/<USERNAME>``).

Whew! You are now ready to start using Pydra!


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
To add your own widgets to the Pydra GUI, make a subclass of ``ModuleWidget`` and add it to your worker's module.

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



For more details about using pydra, see the complete `User Guide <https://duncanmearns.github.io/pydra/>`_.

