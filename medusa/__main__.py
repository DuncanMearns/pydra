from .GUI import *
from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import sys


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, app, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)

        self.app = app

        # Setup window
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.setWindowTitle('Medusa Experiment Control: v1.0')
        self.resize(200, 150)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.w.setLayout(self.layout)

        self.layout_camera = QtWidgets.QHBoxLayout()
        self.camera_label = QtWidgets.QLabel('Select camera:')
        self.layout_camera.addWidget(self.camera_label)
        self.camera_dropdown = QtWidgets.QComboBox()
        self.camera_dropdown.addItem('Pike')
        self.layout_camera.addWidget(self.camera_dropdown)
        self.layout.addLayout(self.layout_camera)

        self.layout_gui = QtWidgets.QHBoxLayout()
        self.optogenetics_checkbox = QtWidgets.QCheckBox('Optogenetics')
        self.tailtrcaker_checkbox = QtWidgets.QCheckBox('Tail tracking')
        self.layout_gui.addWidget(self.optogenetics_checkbox)
        self.layout_gui.addWidget(self.tailtrcaker_checkbox)
        self.layout.addLayout(self.layout_gui)

        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.setFixedSize(150, 50)
        self.start_button.clicked.connect(self.start)
        self.layout.addWidget(self.start_button)

    def start(self):
        camera = str(self.camera_dropdown.currentText())
        gui_constructors = [CameraGUI]
        if self.optogenetics_checkbox.isChecked():
            gui_constructors.append(OptogeneticsGUI)
        if self.tailtrcaker_checkbox.isChecked():
            gui_constructors.append(TailTrackerGUI)
        gui_constructors = tuple(gui_constructors[::-1])
        window = type('GUI', gui_constructors, {})(self)
        window.add_gui_components()
        window.show()
        self.hide()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.app.setQuitOnLastWindowClosed(True)
        a0.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pg.setConfigOptions(useOpenGL=True)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())
