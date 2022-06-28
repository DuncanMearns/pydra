from .images import icons
from PyQt5 import QtCore, QtWidgets, QtGui


class StartWindow(QtWidgets.QSplashScreen):

    quit_signal = QtCore.pyqtSignal()
    file_selected = QtCore.pyqtSignal(str)

    def __init__(self, *args):
        super().__init__(*args)
        # Window layout
        self.setLayout(QtWidgets.QVBoxLayout())
        # Logo
        # im = get_image("python_logo.png")
        im = icons["python_logo"]
        im = im.scaledToWidth(300)
        self.label = QtWidgets.QLabel()
        self.label.setPixmap(im)
        self.layout().addWidget(self.label)
        # Load button
        self.load_button = QtWidgets.QPushButton("LOAD CONFIGURATION")
        self.load_button.clicked.connect(self.load_clicked)
        self.layout().addWidget(self.load_button)
        # Quit button
        self.quit_button = QtWidgets.QPushButton("QUIT")
        self.quit_button.clicked.connect(self.quit_signal)
        self.layout().addWidget(self.quit_button)

    @QtCore.pyqtSlot()
    def load_clicked(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open pydra config", "", "Python files (*.py)")
        if fname:
            self.file_selected.emit(fname)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        """Override QSplashScreen event to ensure window does not disappear when clicked."""
        a0.accept()
