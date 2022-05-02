from PyQt5 import QtWidgets, QtCore, QtGui
import importlib.util
from pydra import Pydra
from pydra.gui import StartWindow, images  #, MainWindow


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, pydra, *args):
        super().__init__(*args)
        self.pydra = pydra
        # Start the pydra event loop
        self.pydra.setup()
        # Set window title
        self.setWindowTitle("Pydra - Experiment Control")
        # Set window icon
        self.setWindowIcon(QtGui.QIcon(images.icons["python_logo"]))
        # Create the state machine
        # self._create_state_machine()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.pydra.exit()
        a0.accept()


class PydraApp(QtWidgets.QApplication):
    """Application for running Pydra GUI."""

    hasConfig = QtCore.pyqtSignal()  # signal emitted when config is set

    @staticmethod
    def run():
        """Static method to run the PydraApp."""
        import sys
        app = PydraApp(sys.argv)
        app.start()
        return sys.exit(app.exec())

    def __init__(self, argv):
        super().__init__(argv)
        self.aboutToQuit.connect(self.closeAllWindows, QtCore.Qt.QueuedConnection)  # ensure always quits
        self.hasConfig.connect(self.main, QtCore.Qt.QueuedConnection)  # run main when config is specified
        if len(argv) > 1:  # take config filepath from argv if exists
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
        pydra = self.pydra_instance(self.config)
        self.main_window = MainWindow(pydra)
        self.main_window.show()
        self.start_window.finish(self.main_window)

    @staticmethod
    def pydra_instance(config: dict):
        """Return a configured pydra instance."""
        Pydra.configure(config=config)
        pydra = Pydra()
        return pydra

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

    @staticmethod
    def config_from_file(pypath):
        """Static method to import a config dictionary from a given python file."""
        if not pypath.endswith(".py"):
            raise ValueError("Path is not a python file.")
        try:
            spec = importlib.util.spec_from_file_location("pydra_config", pypath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
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
