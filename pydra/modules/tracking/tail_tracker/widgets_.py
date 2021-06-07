"""
OLD WIDGET CODE FOR TAIL TRACKER. NEEDS TO BE UPDATED FOR NEW VERSION OF PYDRA.
"""
# from pydra_old.gui.widget import PluginWidget
# from PyQt5 import QtWidgets, QtCore
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# import time
# import numpy as np
#
#
# class TailTrackingWidget(PluginWidget):
#
#     def __init__(self, plugin, *args, **kwargs):
#         super().__init__(plugin, *args, **kwargs)
#         self.setWindowTitle('Tail tracking')
#         # Set tail points
#         self.initialize_tail_button = QtWidgets.QPushButton('Initialize tail points')
#         self.initialize_tail_button.clicked.connect(self.initialize_tail_points)
#         self.widget().layout().addWidget(self.initialize_tail_button, 0, 0, 1, 2)
#         # Number of points
#         self.n_point_setter = QtWidgets.QSpinBox()
#         self.n_point_setter.setMinimum(3)
#         self.n_point_setter.setMaximum(20)
#         self.n_point_setter.setValue(self.plugin.params['n_points'])
#         self.n_point_setter.valueChanged.connect(self.plugin.update_n_points)
#         self.widget().layout().addWidget(QtWidgets.QLabel('N points:'), 0, 2, alignment=QtCore.Qt.AlignRight)
#         self.widget().layout().addWidget(self.n_point_setter, 0, 3)
#
#     def initialize_tail_points(self):
#         ret, points = TailInitialisation.get_new_points(self.plugin.pydra.handler)
#         if ret and (len(points) == 2):
#             self.plugin.update_tail_points(points)
#
#     def idle(self):
#         self.setEnabled(True)
#
#     def live(self):
#         self.setEnabled(False)
#
#     def record(self):
#         self.setEnabled(False)
#
#
# class TailInitialisation(QtWidgets.QDialog):
#
#     def __init__(self, handler):
#         super().__init__()
#         # Give dialog access to handler to receive frames
#         self.handler = handler
#         # Make modal (i.e. freeze main window until this one is close)
#         self.setModal(True)
#         # Resize window
#         self.resize(800, 600)
#         # Set layout
#         self.setLayout(QtWidgets.QHBoxLayout())
#
#         # Create figure for plotting
#         self.figure = Figure()
#         self.canvas = FigureCanvas(self.figure)
#         self.layout().addWidget(self.canvas)
#         self.ax = self.figure.add_subplot(111)
#         self.ax.set_title('LEFT: new point, RIGHT: delete point')
#         self.ax.axis('off')
#
#         # Image to show
#         self.image = None
#         # Draw points
#         self.path, = self.ax.plot([], [], 'o-', color='y', lw=3)
#         self.points = []
#         # Handle mouse click events
#         self.mouse_button_events = {1: self.add_point, 3: self.clear}
#         self.canvas.mpl_connect('button_press_event', self.mouse_button_pressed)
#
#         # Initialize the plots in the axis
#         self.new()
#
#         # Create button for grabbing new image from cameras
#         button_layout = QtWidgets.QVBoxLayout()
#         self.layout().addLayout(button_layout)
#         button_layout.setAlignment(QtCore.Qt.AlignTop)
#         self.newbutton = QtWidgets.QPushButton('New image')
#         self.newbutton.setFixedSize(100, 50)
#         self.newbutton.clicked.connect(self.new)
#         button_layout.addWidget(self.newbutton)
#         # Button for accepting new points
#         self.acceptbutton = QtWidgets.QPushButton('OK')
#         self.acceptbutton.setFixedSize(100, 50)
#         button_layout.addWidget(self.acceptbutton)
#         self.acceptbutton.clicked.connect(self.accept)
#         # Button for cancel
#         self.cancelbutton = QtWidgets.QPushButton('Cancel')
#         self.cancelbutton.setFixedSize(100, 30)
#         button_layout.addWidget(self.cancelbutton)
#         self.cancelbutton.clicked.connect(self.reject)
#
#     def new(self):
#         self.get_image()
#         self.update_axes()
#
#     def get_image(self):
#         self.handler.set_saving(False)
#         self.handler.start_event_loop()
#         time.sleep(0.1)  # give event loop time to start
#         data_from_tracker = []
#         while len(data_from_tracker) < 1:
#             self.handler.send_event(self.handler.tracking_name, 'send_to_gui', ())
#             ret, data = self.handler.receive_event(self.handler.tracking_name, wait=0.05)
#             if ret and data is not None:
#                 data_from_tracker.append(data)
#         self.handler.stop_event_loop()
#         self.image = data_from_tracker[0].frame
#
#     def update_axes(self):
#         if self.image is not None:
#             img = np.asarray(self.image / np.max(self.image))
#             try:
#                 self.imgData.set_data(img)
#             except AttributeError:
#                 self.imgData = self.ax.imshow(img, origin='upper', cmap='Greys_r')
#             x = [p[0] for p in self.points]
#             y = [p[1] for p in self.points]
#             self.path.set_data(x, y)
#             self.canvas.draw()
#
#     def mouse_button_pressed(self, event):
#         if not event.inaxes:
#             return
#         self.mouse_button_events[event.button](event)
#
#     def add_point(self, event):
#         if len(self.points) < 2:
#             self.points.append((event.xdata, event.ydata))
#         self.update_axes()
#
#     def clear(self, event):
#         self.points = []
#         self.update_axes()
#
#     def closeEvent(self, event):
#         self.accept()
#
#     @staticmethod
#     def get_new_points(handler):
#         dialog = TailInitialisation(handler)
#         result = dialog.exec_()
#         points = dialog.points
#         return (result == QtWidgets.QDialog.Accepted), points
