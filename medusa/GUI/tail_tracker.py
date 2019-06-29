from .camera import CameraGUI
from medusa.tracking import TailTracker
from medusa.saving import TailSaver
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import collections
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np


buttonWidth = 100
buttonHeight = 20


class TailInitialisation(QtWidgets.QDialog):

    def __init__(self, camera_thread):
        super(TailInitialisation, self).__init__()
        # Give window access to cameras
        self.camera_thread = camera_thread
        # Make modal (i.e. freeze main window until this one is close)
        self.setModal(True)
        # Resize window
        self.resize(800, 600)

        # Set layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # Create figure for plotting
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.ax.axis('off')
        self.get_image_from_camera()
        time.sleep(0.1)

        # Create button for grabbing new image from cameras
        button_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(button_layout)
        button_layout.setAlignment(QtCore.Qt.AlignTop)
        self.newbutton = QtWidgets.QPushButton('New image')
        self.newbutton.setFixedSize(buttonWidth, buttonHeight)
        self.newbutton.clicked.connect(self.get_image_from_camera)
        button_layout.addWidget(self.newbutton)

        # Handle mouse click events
        self.canvas.mpl_connect('button_press_event', self.update_path)
        self.canvas.mpl_connect('motion_notify_event', self.set_location)

        self.ax.set_title('LEFT: new point, RIGHT: delete point')
        self.path, = self.ax.plot([], [], 'o-', color='y', lw=3)
        self.vert = []

        self.x = []
        self.y = []

        self.mouse_button = {1: self._add_point, 3: self._clear}

        # Button for accepting new points
        self.acceptbutton = QtWidgets.QPushButton('Accept')
        self.acceptbutton.setFixedSize(buttonWidth, 2 * buttonHeight)
        button_layout.addWidget(self.acceptbutton)
        self.acceptbutton.clicked.connect(self.accept)

        # Button for cancel
        self.cancelbutton = QtWidgets.QPushButton('Cancel')
        self.cancelbutton.setFixedSize(buttonWidth, buttonHeight)
        button_layout.addWidget(self.cancelbutton)
        self.cancelbutton.clicked.connect(self.reject)

    def get_image_from_camera(self):
        self.camera_thread.newframe.connect(self.update_image)
        self.camera_thread.acquiring = True

    def update_image(self, indexed_frame):
        self.camera_thread.acquiring = False
        self.camera_thread.newframe.disconnect(self.update_image)
        img = indexed_frame[-1]
        img = np.asarray(img/np.max(img))
        try:
            self.imgData.set_data(img)
        except AttributeError:
            self.imgData = self.ax.imshow(img, origin='upper', cmap='Greys_r')
        self.canvas.draw()

    def set_location(self, event):
        if event.inaxes:
            self.x = event.xdata
            self.y = event.ydata

    def _add_point(self):
        if len(self.vert) < 2:
            self.vert.append((self.x, self.y))

    def _clear(self):
        self.vert = []

    def update_path(self, event):

        # If the mouse pointer is not on the canvas, ignore buttons
        if not event.inaxes: return

        # Do whichever action correspond to the mouse button clicked
        self.mouse_button[event.button]()

        x = [self.vert[k][0] for k in range(len(self.vert))]
        y = [self.vert[k][1] for k in range(len(self.vert))]
        self.path.set_data(x, y)
        self.canvas.draw()

    def closeEvent(self, event):
        self.accept()

    @staticmethod
    def get_new_points(camera_thread):
        dialog = TailInitialisation(camera_thread)
        result = dialog.exec_()
        points = dialog.vert
        return points, result == QtWidgets.QDialog.Accepted


class TailTrackerGUI(CameraGUI):

    def __init__(self, *args, **kwargs):
        super(TailTrackerGUI, self).__init__(*args, **kwargs)
        self.setWindowTitle('Tail tracker')
        self.resize(400, 800)
        # Set tracking object
        self.tracker = TailTracker
        self.tracking_kwargs = {}
        # Set saving object
        self.saver = TailSaver
        self.saving_kwargs = {}
        # Create caches
        self.tail_point_cache = collections.deque(maxlen=self._frame_buffer)
        self.tail_angle_cache = collections.deque(maxlen=self._frame_buffer)
        self.caches.append(self.tail_point_cache)
        self.caches.append(self.tail_angle_cache)
        # -------------
        # Add new plots
        # -------------
        # Tail points
        self.tail_points = self.img_plot.plot([], [], pen=None, symbol='o')
        # Tail angle
        self.tail_angle_plot = self.layout_data_plots.addPlot(row=1, col=0)
        self.tail_angle_plot.showGrid(x=True, y=True)
        self.tail_angle_plot.setLabel('left', 'Tail angle', 'deg')
        self.tail_angle_plot.setRange(yRange=[-30, 30])
        self.tail_angle_plot.setAutoPan(x=True)
        self.tail_angle_plot.setLimits(minXRange=1000)
        self.tail_angle = self.tail_angle_plot.plot([], [], pen=(255, 0, 0))

    def tracker_init(self):
        if not 'head' in self.tracking_kwargs.keys() or not 'tail_length' in self.tracking_kwargs.keys():
            points, ret = TailInitialisation.get_new_points(self.camera_thread)
            if ret and len(points) == 2:
                tail = np.asarray(points)
                tail = np.asarray([[int(i[0]), int(i[1])] for i in tail])
                self.tracking_kwargs['head'] = tail[0]
                self.tracking_kwargs['tail_length'] = tail[1, 0] - tail[0, 0] + 10
                return True
            else:
                return False
        else:
            return True

    def update_plots(self):
        if self.camera_thread.acquiring:
            try:
                # Show the new image
                i, timestamp, laser_status, img = self.frame_cache_output[-1]
                img = np.asarray(img/np.max(img))
                self.img.setImage(img[::-1, :].T)
                # Show tail points
                tail_points = self.tail_point_cache[-1]
                self.tail_points.setData(tail_points[:, 0], self.frameSize[1] - tail_points[:, 1])
                # Update tail angle
                tail_angle = np.array(self.tail_angle_cache)
                t = np.arange(len(tail_angle))
                self.tail_angle.setData(t, tail_angle)
                # Update cameras and buffer info
                self._change_camera_message()
            except IndexError:  # No data to show
                pass
