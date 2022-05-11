from PyQt5 import QtWidgets, QtCore

from ..states import Stateful
# from .directory_widget import DirectoryWidget
# from .file_naming import FileNamingWidget
# from .protocol_widget import ProtocolWidget

from pathlib import Path


BUTTON_WIDTH = 100
BUTTON_HEIGHT = 50


class RecordButton(Stateful, QtWidgets.QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__("RECORD", *args, **kwargs)
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))
        self.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)

    def enterIdle(self):
        self.setEnabled(True)
        self.setText("RECORD")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaPlay')))

    def enterRunning(self):
        self.setText("ABORT")
        self.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_MediaStop')))


def checked(method):
    def check_naming_conflict(toolbar, val):
        directory = Path(toolbar.directory_widget.directory)
        filename = toolbar.filename_widget.filename
        if filename:
            conflicts = list(directory.glob(f"{filename}*"))
            if len(conflicts):
                paths = "\n".join([str(conflict) for conflict in conflicts])
                dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                               "Warning",
                                               f"File already exists!\n\n{paths}",
                                               parent=toolbar)
                dialog.show()
        return method(toolbar, val)
    return check_naming_conflict


class RecordingToolbar(Stateful, QtWidgets.QToolBar):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # Set params
        self.setFloatable(False)
        self.setMovable(False)
        # Record button
        self.record_button = RecordButton()
        self.stateMachine.idle.addTransition(self.record_button.clicked, self.stateMachine.running)
        self.stateMachine.running.addTransition(self.record_button.clicked, self.stateMachine.idle)
        self.addWidget(self.record_button)
        self.addSeparator()
        # # Directory widget
        # self.directory_widget = DirectoryWidget(self.parent().pydra.working_dir)
        # self.addWidget(self.directory_widget)
        # self.addSeparator()
        # # File naming widget
        # self.filename_widget = FileNamingWidget()
        # self.addWidget(self.filename_widget)
        # self.addSeparator()
        # # Protocol widget
        # self.protocol_widget = ProtocolWidget()
        # self.protocol_widget.editor_clicked.connect(self.show_protocol)
        # self.addWidget(self.protocol_widget)
        # # Signals
        # self.directory_widget.changed.connect(self.set_working_directory)
        # self.filename_widget.changed.connect(self.set_filename)

    @checked
    def set_filename(self, filename):
        self.parent().pydra.set_filename(filename)

    @checked
    def set_working_directory(self, directory):
        self.parent().pydra.set_working_directory(directory)

    def show_protocol(self):
        self.parent().protocol_window.show()
