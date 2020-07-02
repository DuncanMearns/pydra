from pipeline import MedusaPipeline
from multiprocessing import Event, Pipe
import time
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
import sys


class Medusa(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Layout sizes
        self.main_width = 1000
        self.main_height = 800
        self.button_width = 100
        self.button_height = 20

        # Setup main window
        self.setWindowTitle('Medusa Experiment Control Centre')
        self.resize(self.main_width, self.main_height)
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.w.setLayout(self.main_layout)

        # self.display_widget = QtWidgets.QWidget()
        # self.display_widget.setLayout(QtWidgets.QGridLayout())

        self.display_widget = pg.GraphicsLayoutWidget()
        self.main_layout.addWidget(self.display_widget)
        self.image = pg.ImageItem()
        self.image_plot = self.display_widget.addPlot(**kwargs)
        self.image_plot.setMouseEnabled(False, False)
        self.image_plot.setAspectLocked()
        self.image_plot.hideAxis('bottom')
        self.image_plot.hideAxis('left')
        self.image_plot.addItem(self.image)

        self.button_widget = QtWidgets.QWidget()
        self.button_widget.setLayout(QtWidgets.QHBoxLayout())
        self.main_layout.addWidget(self.button_widget)

        self.button_start = QtWidgets.QPushButton("START")
        self.button_start.clicked.connect(self.start_pipeline)
        self.button_widget.layout().addWidget(self.button_start)

        self.button_stop = QtWidgets.QPushButton("STOP")
        self.button_stop.clicked.connect(self.stop_pipeline)
        self.button_widget.layout().addWidget(self.button_stop)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_gui)

        self.update_gui_event = Event()
        self.parent_conn, self.child_conn = Pipe(False)
        self.pipeline = MedusaPipeline(self.update_gui_event, self.child_conn)

    @QtCore.pyqtSlot()
    def start_pipeline(self):
        self.pipeline.start()
        self.timer.start(50)

    @QtCore.pyqtSlot()
    def stop_pipeline(self):
        self.pipeline.stop()
        self.timer.stop()

    @QtCore.pyqtSlot()
    def update_gui(self):
        self.update_gui_event.set()
        frames = []
        while True:
            data = self.parent_conn.recv()
            if data is None:
                break
            else:
                frames.append(data)
        if len(frames):
            frame = frames[-1].frame
            self.image.setImage(frame[::-1, :].T)

    @staticmethod
    def run():
        app = QtWidgets.QApplication([])
        window = Medusa()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    Medusa.run()
    # pipeline = MedusaPipeline()
    # pipeline.start()
    # time.sleep(5)
    # pipeline.stop()
