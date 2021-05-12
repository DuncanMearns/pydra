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
