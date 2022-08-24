import traceback
import warnings

from PyQt5 import QtWidgets, QtCore
import importlib.util
from pydra.pydra import Pydra
from pydra.gui import StartWindow, MainWindow
import sys
import os


class PydraApp(QtWidgets.QApplication):
    """Application for running Pydra GUI."""

    hasConfig = QtCore.pyqtSignal()  # signal emitted when config is set

    @staticmethod
    def run(config=None):
        """Static method to run the PydraApp."""
        import sys
        app = PydraApp(sys.argv, config)
        app.start()
        return sys.exit(app.exec())

    def __init__(self, argv, config: dict = None):
        super().__init__(argv)
        self.aboutToQuit.connect(self.closeAllWindows, QtCore.Qt.QueuedConnection)  # ensure always quits
        self.hasConfig.connect(self.main, QtCore.Qt.QueuedConnection)  # run main when config is specified
        if config:
            self.config_file = "user provided"
            self.config = config
        elif len(argv) > 1:  # take config filepath from argv if exists
            self.config_file = argv[1]
            self.config = self.config_from_file(self.config_file)

    def start(self):
        """Create a start window to load config."""
        self.start_window = StartWindow()
        self.start_window.quit_signal.connect(self.quit, QtCore.Qt.QueuedConnection)
        self.start_window.file_selected.connect(self.load_config)
        self.start_window.show()

    @QtCore.pyqtSlot()
    def main(self):
        """Create a main window with a configured pydra instance."""
        self.start_window.setEnabled(False)
        self.start_window.showMessage(f"Starting pydra with config from {self.config_file}")
        pydra = Pydra.run(config=self.config)
        # Check config
        if not len(pydra.config_modules):
            warnings.warn("No modules are specified in the config.")
        if not len(pydra.config_savers):
            warnings.warn("No savers are specified in the config - data will not be saved!")
        # Show main window
        try:
            self.main_window = MainWindow(pydra)
        except Exception:
            print(traceback.format_exc())
            pydra.exit()
            sys.exit(-1)
        self.main_window.show()
        self.start_window.finish(self.main_window)

    @property
    def config(self):
        try:
            return self._config
        except AttributeError:
            return {}

    @config.setter
    def config(self, d: dict):
        if not isinstance(d, dict):
            return
        self._config = d
        self.hasConfig.emit()

    @QtCore.pyqtSlot(str)
    def load_config(self, pypath):
        """Slot to load a config from the given python file."""
        self.config_file = pypath
        self.config = self.config_from_file(pypath)
        print(self.config)

    @staticmethod
    def config_from_file(pypath):
        """Static method to import a config dictionary from a given python file."""
        if not pypath.endswith(".py"):
            raise ValueError("Path is not a python file.")
        try:
            dirname, modname = os.path.split(pypath)
            modname = modname.split(".")[0]
            sys.path.append(dirname)
            spec = importlib.util.spec_from_file_location(modname, pypath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[modname] = mod
        except FileNotFoundError:
            print("Path to stimulus file does not exist.")
            return
        except Exception as e:
            print(e)
            return
        try:
            config = mod.config
            assert isinstance(config, dict)
            return config
        except AttributeError:
            print(f"{pypath} does not contain config.")
        except AssertionError:
            print("config variable is not a dictionary.")
        return
