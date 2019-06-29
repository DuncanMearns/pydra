from .GUI import *
from PyQt5 import QtWidgets
import pyqtgraph as pg
import sys


class MainWindow(QtWidgets.QMainWindow):

    GUIs = {'Camera': CameraGUI,
            'TailTracker': TailTrackerGUI}

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Setup window
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.setWindowTitle('Medusa Experiment Control: v1.0')
        self.resize(200, 150)
        self.layout = QtWidgets.QVBoxLayout()
        self.w.setLayout(self.layout)

        self.layout_camera = QtWidgets.QHBoxLayout()
        self.camera_label = QtWidgets.QLabel('Select camera:')
        self.layout_camera.addWidget(self.camera_label)
        self.camera_dropdown = QtWidgets.QComboBox()
        self.camera_dropdown.addItem('Pike')
        self.layout_camera.addWidget(self.camera_dropdown)
        self.layout.addLayout(self.layout_camera)

        self.layout_gui = QtWidgets.QHBoxLayout()
        self.gui_label = QtWidgets.QLabel('Select GUI:')
        self.layout_gui.addWidget(self.gui_label)
        self.gui_dropdown = QtWidgets.QComboBox()
        self.gui_dropdown.addItem('Camera')
        self.gui_dropdown.addItem('TailTracker')
        self.layout_gui.addWidget(self.gui_dropdown)
        self.layout.addLayout(self.layout_gui)

        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.clicked.connect(self.start)
        self.layout.addWidget(self.start_button)

    def start(self):
        camera = str(self.camera_dropdown.currentText())
        gui = str(self.gui_dropdown.currentText())
        window = self.GUIs[gui](self)
        window.show()
        self.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    pg.setConfigOptions(useOpenGL=True)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
