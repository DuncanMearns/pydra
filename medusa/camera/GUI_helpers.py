from pyqtgraph.Qt import QtCore, QtGui, QtWidgets


class CameraWaitMessage(QtWidgets.QDialog):

    def __init__(self, parent):
        super(CameraWaitMessage, self).__init__()

        self.setModal(True)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.parent = parent

        layout = QtWidgets.QHBoxLayout()
        msg = QtWidgets.QLabel('Connecting to camera. Please wait...')
        layout.addWidget(msg)
        self.setLayout(layout)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.check_connection)
        self.timer.start()

    def check_connection(self):
        if self.parent.camera_thread.connected:
            self.close()

    @staticmethod
    def run(parent):
        msg = CameraWaitMessage(parent)
        msg.exec_()


class CameraSettings(QtWidgets.QDialog):

    def __init__(self, wh, fps):
        super(CameraSettings, self).__init__()
        # Set modal
        self.setModal(True)
        # Camera settings
        self.width, self.height = wh
        self.framerate = fps

        layout = QtWidgets.QFormLayout()
        int_validator = QtGui.QIntValidator()
        width_label = QtWidgets.QLabel('Width:')
        self.width_le = QtWidgets.QLineEdit(str(self.width))
        self.width_le.setValidator(int_validator)
        layout.addRow(width_label, self.width_le)

        height_label = QtWidgets.QLabel('Height:')
        self.height_le = QtWidgets.QLineEdit(str(self.height))
        self.height_le.setValidator(int_validator)
        layout.addRow(height_label, self.height_le)

        fps_label = QtWidgets.QLabel('Frame rate:')
        self.fps_le = QtWidgets.QLineEdit(str(self.framerate))
        self.fps_le.setValidator(int_validator)
        layout.addRow(fps_label, self.fps_le)

        # Ok / cancel
        self.okbutton = QtWidgets.QPushButton('OK')
        self.okbutton.setFixedSize(100, 25)
        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton = QtWidgets.QPushButton('Cancel')
        self.cancelbutton.setFixedSize(100, 25)
        self.cancelbutton.clicked.connect(self.reject)
        layout.addRow(self.okbutton, self.cancelbutton)

        self.setLayout(layout)
        self.setWindowTitle('Camera settings')

    @staticmethod
    def change(wh, fps):
        dialog = CameraSettings(wh, fps)
        result = dialog.exec_()
        width = int(str(dialog.width_le.text()))
        height = int(str(dialog.height_le.text()))
        framerate = int(str(dialog.fps_le.text()))
        settings = dict(wh=(width, height), fps=framerate)
        return (result == QtWidgets.QDialog.Accepted), settings
