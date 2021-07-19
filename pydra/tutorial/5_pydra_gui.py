from pydra import Pydra, config, ports
from pydra.core.workers import Worker
from pydra.gui import ControlWidget  # import the ModuleWidget class
from PyQt5 import QtWidgets, QtCore  # import from PyQt


class HelloWorld(Worker):
    """Worker class"""

    name = "hello_world"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add an event called "hello_world" to the worker and map it to a corresponding method
        self.events["hello_world"] = self.hello_world

    def hello_world(self, **kwargs):
        """Method called when pydra sends the 'hello_world' event."""
        print("")
        print("Hello world button was clicked.")
        print(f"The source of the message was {kwargs['source']}.")
        print(f"The target of the message is {kwargs['target']}.")


# Create a widget for the Pydra GUI
class HelloWidget(ControlWidget):
    """The ModuleWidget is just a wrapper for the PyQt DockWidget class which has access to the main Pydra instance and
    implements some other useful functions."""

    plot = None  # we can set the widget's plot attribute to None if we do not want to plot any data from the worker

    def __init__(self, *args, **kwargs):
        # As with the other classes in Pydra, subclasses should always include the call to super()
        super().__init__(*args, **kwargs)
        # Create a button for our widget
        self.button = QtWidgets.QPushButton("HELLO WORLD")
        # Connect the button's "clicked" signal to our widget's button_clicked slot
        self.button.clicked.connect(self.button_clicked)
        # Set the main widget to be our button
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.button)

    @QtCore.pyqtSlot()
    def button_clicked(self):
        """Method called whenever the button in the widget is clicked"""
        self.send_event("hello_world")  # send_event method can be used just like we were calling it from Pydra


# Create a module for our HelloWorld worker
HELLOWORLD = {
    "worker": HelloWorld,
    "controller": HelloWidget  # add our widget to the module - this will add our widget to the Pydra GUI!
}


# Add the HELLOWORLD module to config
config["modules"] = [HELLOWORLD]


if __name__ == "__main__":

    # Configure 0MQ connections
    Pydra.configure(config, ports)

    # To run the Pydra GUI, we must instantiate the main pydra class using it's run method
    pydra = Pydra.run(**config)

    # At this point the Qt event loop has started, and the script will exit when the GUI is closed.
    # Code beyond this point cannot be reached.
    print("HELP! You cannot reach me!")
