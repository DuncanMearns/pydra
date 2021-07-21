from pydra.gui import Plotter
from PyQt5 import QtCore, QtWidgets
from desktopmagic import screengrab_win32 as grab
import numpy as np


class ScreenGrabber(Plotter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addOptions()
        self.addImagePlot("screen")
        # Create timer
        self.screenTimer = QtCore.QTimer()
        self.screenTimer.setInterval(self.updateSpinBox.value())
        self.screenTimer.timeout.connect(self.grab)
        self.screenTimer.start()

    def addOptions(self):
        self.options = QtWidgets.QWidget()
        self.options.setLayout(QtWidgets.QFormLayout())
        # Spinbox for controlling screen number
        self.screenSpinBox = QtWidgets.QSpinBox()
        self.screenSpinBox.setMinimum(0)
        self.screenSpinBox.setMaximum(len(grab.getDisplayRects()) - 1)
        self.options.layout().addRow("Screen #", self.screenSpinBox)
        # Spinbox for controlling update rate
        self.updateSpinBox = QtWidgets.QSpinBox()
        self.updateSpinBox.setMinimum(20)
        self.updateSpinBox.setMaximum(1000)
        self.updateSpinBox.setValue(50)
        self.updateSpinBox.valueChanged.connect(self.reset_timer)
        self.options.layout().addRow("Update (ms)", self.updateSpinBox)
        # Spinbox for controlling downsampling rate
        self.downsamplingSpinBox = QtWidgets.QSpinBox()
        self.downsamplingSpinBox.setMinimum(1)
        self.downsamplingSpinBox.setValue(5)
        self.options.layout().addRow("Downsampling", self.downsamplingSpinBox)
        # Add options panel
        policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        self.options.setSizePolicy(policy)
        self.options_proxy = QtWidgets.QGraphicsProxyWidget()
        self.options_proxy.setWidget(self.options)
        self.addItem(self.options_proxy)

    @QtCore.pyqtSlot()
    def grab(self):
        rects = grab.getDisplayRects()
        img = np.array(grab.getRectAsImage(rects[self.screenSpinBox.value()]))
        downsampling = self.downsamplingSpinBox.value()
        img = img[::downsampling, ::downsampling]
        self.updateImage("screen", img)

    @QtCore.pyqtSlot(int)
    def reset_timer(self, msec):
        self.screenTimer.stop()
        self.screenTimer.start(msec)
