from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import sys
from vimba import PikeCamera
import numpy as np
from anytree import Node
from multiprocessing import Process, Pipe, Event, Queue
import time
from collections import namedtuple
from processes import AcquisitionProcess, TrackingProcess, SavingProcess
import multiprocessing as mp


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, app, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.app = app

        # Setup window
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.setWindowTitle('Medusa Experiment Control: v1.0')
        self.resize(800, 600)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.w.setLayout(self.layout)

        # Create a GraphicsLayoutWidget to add plots
        layout_user_proxy = QtWidgets.QHBoxLayout()
        self.layout_user_plots = pg.GraphicsLayoutWidget()
        layout_user_proxy.addWidget(self.layout_user_plots)
        self.layout.addLayout(layout_user_proxy)

        """Adds a plot for displaying images from the camera to the GUI

        Parameters
        ----------
        row : int
            row number passed to GraphicsLayoutWidget addPlot method
        col : int
            column number passed to GraphicsLayoutWidget addPlot method
        """
        self.image = pg.ImageItem()
        self.image_plot = self.layout_user_plots.addPlot(**kwargs)
        self.image_plot.setMouseEnabled(False, False)
        self.image_plot.setAspectLocked()
        self.image_plot.hideAxis('bottom')
        self.image_plot.hideAxis('left')
        self.image_plot.addItem(self.image)

        self.button1 = QtWidgets.QPushButton('Start')
        self.button1.clicked.connect(self.start)
        self.layout.addWidget(self.button1)

        self.button2 = QtWidgets.QPushButton('Stop')
        self.button2.clicked.connect(self.stop)
        self.layout.addWidget(self.button2)

        mp.set_start_method("spawn", force=True)

    def start(self):
        frame_q = Queue()
        tracking_q = Queue()
        self.exit_flag = Event()
        self.grabber = CameraAcquisition(q_out=frame_q, exit_flag=self.exit_flag)

        self.tracker = DummyTracker(q_in=frame_q, q_out=tracking_q, exit_flag=self.exit_flag)
        self.saver = DummySaver(q_in=tracking_q, exit_flag=self.exit_flag)

        self.saver.start()
        self.tracker.start()
        self.grabber.start()

    def stop(self):

        self.exit_flag.set()

        self.grabber.join()
        self.tracker.join()
        self.saver.join()

        print('All processes terminated.')


class DummyTracker(TrackingProcess):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self, *args):
        print(args[0].shape)
        return args


class DummySaver(SavingProcess):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# =============================================================

class Grabber(Node):

    def __init__(self, name):
        super().__init__(name, parent=None)


class Tracker(Node):

    def __init__(self, name, parent):
        super().__init__(name, parent=parent)


class Saver(Node):

    def __init__(self, name, parent):
        super().__init__(name, parent=parent)


class Display(Node):

    def __init__(self, name, parent):
        super().__init__(name, parent=parent)

# =============================================================

class PikeGrabber(Grabber):

    def __init__(self):
        super().__init__('PikeGrabber', )

    def setup(self):
        self.camera = PikeCamera()
        self.camera.open_camera()

    def acquire(self):
        return self.camera.read()

    def cleanup(self):
        self.camera.release()


class MedusaPipeline:

    def __init__(self):
        pass

    def start(self):
        # frame_q = Queue()
        # tracking_q = Queue()
        # self.exit_flag = Event()
        # self.grabber = CameraAcquisition(q_out=frame_q, exit_flag=self.exit_flag)
        #
        # self.tracker = DummyTracker(q_in=frame_q, q_out=tracking_q, exit_flag=self.exit_flag)
        # self.saver = DummySaver(q_in=tracking_q, exit_flag=self.exit_flag)
        #
        # self.saver.start()
        # self.tracker.start()
        # self.grabber.start()

    def stop(self):
        # self.exit_flag.set()
        #
        # self.grabber.join()
        # self.tracker.join()
        # self.saver.join()
        #
        # print('All processes terminated.')





def main():
    app = QtWidgets.QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)
    pg.setConfigOptions(useOpenGL=True)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
