from PyQt5 import QtWidgets, QtCore
from .buttons import RecordButton
from .file_naming import FileNamingWidget
from .trial_control import TrialControlWidget
from .trial_structure import TrialStructureWidget


class ExperimentWidget(QtWidgets.QWidget):

    # File naming
    directory_changed = QtCore.pyqtSignal(str)
    filename_changed = QtCore.pyqtSignal(str)
    trial_number_changed = QtCore.pyqtSignal(int)
    # Trial control
    n_trials_changed = QtCore.pyqtSignal(int)
    inter_trial_interval_changed = QtCore.pyqtSignal(int)
    # Protocol
    protocol_changed = QtCore.pyqtSignal(list)

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
        # Propagate signals
        self.file_naming_widget.directory_changed.connect(self.directory_changed)
        self.file_naming_widget.filename_changed.connect(self.filename_changed)
        self.file_naming_widget.trial_number_changed.connect(self.trial_number_changed)
        self.trial_control_widget.n_trials_changed.connect(self.n_trials_changed)
        self.trial_control_widget.inter_trial_interval_changed.connect(self.inter_trial_interval_changed)
        self.protocol_widget.protocol_changed.connect(self.protocol_changed)

    @property
    def filename(self):
        return self.file_naming_widget.filename

    @property
    def directory(self):
        return self.file_naming_widget.directory

    @property
    def trial_number(self):
        return self.file_naming_widget.trial_number

    @property
    def n_trials(self):
        return self.trial_control_widget.n_trials

    @property
    def inter_trial_interval(self):
        return self.trial_control_widget.inter_trial_interval

    @property
    def protocol(self):
        return self.protocol_widget.protocol
