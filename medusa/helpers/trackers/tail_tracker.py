from .tracker_base import TrackerBase
from PyQt5 import QtWidgets, QtCore
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import time
from collections import deque
import numpy as np
import math
import cv2


class TailInitialisation(QtWidgets.QDialog):

    button_width = 100
    button_height = 20

    def __init__(self, camera_thread):
        super().__init__()
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
        self.newbutton.setFixedSize(self.button_width, self.button_height)
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
        self.acceptbutton.setFixedSize(self.button_width, 2 * self.button_height)
        button_layout.addWidget(self.acceptbutton)
        self.acceptbutton.clicked.connect(self.accept)

        # Button for cancel
        self.cancelbutton = QtWidgets.QPushButton('Cancel')
        self.cancelbutton.setFixedSize(self.button_width, self.button_height)
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


class TailTracker(TrackerBase):

    def __init__(self, parent, points_buffer, points_display_buffer, angle_display_buffer):
        super().__init__(parent)
        # Caches
        self.points_cache = deque(maxlen=points_buffer)
        self.points_display_cache = deque(maxlen=points_display_buffer)
        self.angle_display_cache = deque(maxlen=angle_display_buffer)
        # Tracking
        self.tail_length = None
        self.head = None
        self.num_points = 9
        # Saving
        self.points = []
        self.points_path = None

    def initialise_tracking(self, from_button=False):
        if from_button or self.head is None or self.tail_length is None:
            points, ret = TailInitialisation.get_new_points(self.parent.camera_thread)
            if ret and len(points) == 2:
                tail = np.asarray(points)
                tail = np.asarray([[int(i[0]), int(i[1])] for i in tail])
                self.head = tail[0]
                self.tail_length = tail[1, 0] - tail[0, 0] + 10
                return True
            else:
                return False
        else:
            return True

    def track(self, frame_number, timestamp, frame):
        frame = np.asarray(frame / np.max(frame))
        tail_points = [self.head]
        width = self.tail_length
        x = self.head[0]
        y = self.head[1]
        img_filt = np.zeros(frame.shape)
        img_filt = cv2.boxFilter(frame, -1, (7, 7), img_filt)
        lin = np.linspace(0, np.pi, 20)
        for j in range(self.num_points):
            try:
                # Find the x and y values of the arc
                xs = x + width / self.num_points * np.sin(lin)
                ys = y + width / self.num_points * np.cos(lin)
                # Convert them to integer, because of definite pixels
                xs, ys = xs.astype(int), ys.astype(int)
                # ident = np.where(img_filt[ys,xs]==max(img_filt[ys,xs]))[0][0]
                ident = np.where(img_filt[ys, xs] == min(img_filt[ys, xs]))[0][0]
                x = xs[ident]
                y = ys[ident]
                lin = np.linspace(lin[ident] - np.pi / 2, lin[ident] + np.pi / 2, 20)
                # Add point to list
                tail_points.append([x, y])
            except IndexError:
                tail_points.append(tail_points[-1])
        tailangle = float(math.atan2(np.nanmean(np.asarray(tail_points)[-3:-1, 1]) -
                                     np.asarray(tail_points)[0, 1],
                                     np.nanmean(np.asarray(tail_points)[-3:-1, 0]) -
                                     np.asarray(tail_points)[0, 0]) * 180.0 / 3.1415) * (-1)
        tail_points = np.asarray(tail_points)
        self.points_cache.append(tail_points)
        self.points_display_cache.append(tail_points)
        self.angle_display_cache.append(tailangle)

    def clear(self):
        self.points_cache.clear()
        self.points_display_cache.clear()
        self.angle_display_cache.clear()

    def initialise_saving(self, path):
        self.points_path = path + '_points.npy'
        self.points = []
        return True

    def extend(self, frame_data):
        try:
            self.saving_flag = False
            self.points.append(self.points_cache.popleft())
        except IndexError:
            self.saving_flag = True

    def dump(self):
        points = np.array(self.points)
        np.save(self.points_path, points)
