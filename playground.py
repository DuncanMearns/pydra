from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import sys
from vimba import PikeCamera
import numpy as np
from anytree import Node
from multiprocessing import Process, Pipe, Event, Queue
import time
from collections import namedtuple
import multiprocessing as mp

from pipeline import *


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

        grabber = WorkerConstructor(CameraAcquisition, (PikeCamera,), {})
        tracker = WorkerConstructor(Tracker, (), {})
        saver = WorkerConstructor(Saver, (), {})

        self.pipeline = MedusaPipeline(grabber, tracker, saver)
        self.pipeline.start()

        # # ==========================
        # # SETUP DISPLAY UPDATE TIMER
        # # ==========================
        # # Create timer for handling display updates
        # # This ensures that events sent from recording or helpers threads don't queue up waiting to be processed
        # self.display_update_rate = 20  # fps
        # self.timer = QtCore.QTimer()
        # self.timer.setInterval(int(1000 / self.display_update_rate))
        # self.timer.timeout.connect(self.update_plots)
        # self.timer.start()

    def stop(self):
        self.pipeline.stop()

    # def update_plots(self):
    #     self.pipeline.display_queue.get()
        # pass
        # frame = self.tracking_q.get_display()
        # print(frame)


def main():
    app = QtWidgets.QApplication(sys.argv)
    # app.setQuitOnLastWindowClosed(False)
    pg.setConfigOptions(useOpenGL=True)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
