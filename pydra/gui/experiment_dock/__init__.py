from PyQt5 import QtWidgets
from .buttons import RecordButton
from .file_naming import FileNamingWidget
from .trial_control import TrialControlWidget
from .trial_structure import TrialStructureWidget


class ExperimentWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.record_button = RecordButton()
        self.layout().addWidget(self.record_button)
        self.file_naming_widget = FileNamingWidget("", "")
        self.layout().addWidget(self.file_naming_widget)
        self.trial_control_widget = TrialControlWidget(1, 1)
        self.layout().addWidget(self.trial_control_widget)
        self.protocol_widget = TrialStructureWidget()
        self.layout().addWidget(self.protocol_widget)
