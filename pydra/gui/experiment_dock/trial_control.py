from PyQt5 import QtWidgets, QtCore

from ..state_machine import Stateful
from ..helpers import TimeUnitWidget


class TrialControlWidget(Stateful, QtWidgets.QGroupBox):

    def __init__(self, n_trials, inter_trial_time, n_trial_digits=3, inter_trial_unit="s", **kwargs):
        super().__init__("Trials")
        # Layout
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        # --------
        # N trials
        # --------
        self.n_digits = n_trial_digits
        # Label
        self.n_trial_label = QtWidgets.QLabel("N trials:")
        self.n_trial_label.setToolTip("Number of trials")
        # Spinbox
        self.n_trial_spinbox = QtWidgets.QSpinBox()
        self.n_trial_spinbox.setMinimum(1)
        self.n_trial_spinbox.setMaximum(self.n_trials_max)
        self.n_trial_spinbox.valueChanged.connect(self.stateMachine.set_n_trials)
        # Add to layout
        self.layout().addWidget(self.n_trial_label)
        self.layout().addWidget(self.n_trial_spinbox)
        # --------------------
        # Inter-trial interval
        # --------------------
        # Label
        self.inter_trial_label = QtWidgets.QLabel("Interval:")
        self.inter_trial_label.setToolTip("Inter-trial interval")
        # Widget
        self.inter_trial_widget = TimeUnitWidget()
        self.inter_trial_widget.addSeconds(minval=1, maxval=600)
        self.inter_trial_widget.addMinutes(minval=1, maxval=300)
        self.inter_trial_widget.valueChanged.connect(self.stateMachine.set_inter_trial_interval)
        # Add to layout
        self.layout().addWidget(self.inter_trial_label)
        self.layout().addWidget(self.inter_trial_widget)
        # ------------
        # Emit signals
        # ------------
        self.n_trial_spinbox.setValue(n_trials)
        self.inter_trial_widget.change_unit(inter_trial_unit)
        self.inter_trial_widget.setValue(inter_trial_time)

    @property
    def n_trials_max(self):
        return int("1" + "0" * self.n_digits) - 1

    def enterIdle(self):
        self.setEnabled(True)

    def enterRunning(self):
        self.setEnabled(False)
