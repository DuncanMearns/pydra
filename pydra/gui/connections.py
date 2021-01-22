from PyQt5 import QtCore, QtWidgets
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt


class QButtonAdd(QtWidgets.QPushButton):

    button_clicked = QtCore.pyqtSignal(object)

    def __init__(self, group, *args, **kwargs):
        super().__init__("+", *args, **kwargs)
        self.group = group
        self.clicked.connect(self.buttonClicked)
        self.button_clicked.connect(self.group.enterNew)

    def buttonClicked(self):
        self.button_clicked.emit(self)


class QComboBoxLinked(QtWidgets.QComboBox):

    current_index_changed = QtCore.pyqtSignal(object, int)

    def __init__(self, group, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        self.currentIndexChanged.connect(self._currentIndexChanged)
        self.current_index_changed.connect(self.group.indexChanged)
        self.group.updateChildren.connect(self.checkIndex)

    def checkIndex(self, obj, i):
        if obj is not self:
            if self.currentIndex() == i:
                self.setCurrentIndex(self.group.items.index(""))

    def _currentIndexChanged(self, val):
        self.current_index_changed.emit(self, val)


class Editor(QtWidgets.QDialog):

    new_value = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.le = QtWidgets.QLineEdit()
        self.layout().addWidget(self.le)
        self.le.returnPressed.connect(self.newValue)
        self.le.returnPressed.connect(self.close)

    def newValue(self):
        text = self.le.text()
        self.new_value.emit(text.strip())


class ItemAssignmentWidget(QtWidgets.QGroupBox):

    updateChildren = QtCore.pyqtSignal(QComboBoxLinked, int)

    def __init__(self, name, items, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.items = items
        self.combo_boxes = []
        self.buttons = []
        self.setMouseTracking(True)
        self.x, self.y = 0, 0
        self.setLayout(QtWidgets.QGridLayout())
        self.editor = Editor()
        self.editor.new_value.connect(self.changeItem)

    def rowCount(self) -> int:
        return self.layout().rowCount()

    def columnCount(self) -> int:
        return self.layout().columnCount()

    def addRow(self, label, val):
        # Add label
        self.layout().addWidget(QtWidgets.QLabel(label), self.rowCount(), 0)
        # Add combo box
        combo_box = QComboBoxLinked(self)
        combo_box.addItems(self.items)
        if val:
            self.addItem(val)
            idx = self.items.index(val)
            combo_box.setCurrentIndex(idx)
        self.combo_boxes.append(combo_box)
        self.layout().addWidget(combo_box, self.rowCount() - 1, 1)
        # Add button
        add_button = QButtonAdd(self)
        self.buttons.append(add_button)
        self.layout().addWidget(add_button, self.rowCount() - 1, 2)

    def addItem(self, item):
        if item not in self.items:
            self.items.append(item)
            for cb in self.combo_boxes:
                cb.addItem(item)

    def changeItem(self, item):
        self.addItem(item)
        idx = self.buttons.index(self.editor.button)
        self.combo_boxes[idx].setCurrentIndex(self.items.index(item))

    @QtCore.pyqtSlot(object, int)
    def indexChanged(self, obj, val):
        self.updateChildren.emit(obj, val)

    def enterNew(self, button):
        self.editor.button = button
        self.editor.show()

    def getValue(self, name) -> str:
        for i in range(self.rowCount()):
            label = self.layout().itemAtPosition(i, 0)
            if label and (label.widget().text() == name):
                combo_box = self.layout().itemAtPosition(i, 1).widget()
                return combo_box.currentText()


class ConnectivityWidget(QtWidgets.QGroupBox):

    def __init__(self, M, names, *args, **kwargs):
        super().__init__("Connectivity", *args, **kwargs)
        self.M = M
        self.names = names
        self.setLayout(QtWidgets.QHBoxLayout())
        fig, ax = plt.subplots(figsize=np.array(self.M.shape) * 0.5)
        ax.matshow(self.M, cmap="inferno", vmin=0, vmax=self.M.max() * 1.2)
        ax.set_xticks(np.arange(len(self.names)))
        ax.set_xticklabels(self.names, rotation=45)
        ax.set_title("SUBSCRIPTIONS")
        ax.set_yticks(np.arange(len(self.names)))
        ax.set_yticklabels(self.names, rotation=45, va="center")
        for i in range(len(self.names) - 1):
            ax.plot([i + 0.5, i + 0.5], [-0.5, len(self.names) - 0.5], lw=2, c="w")
            ax.plot([-0.5, len(self.names) - 0.5], [i + 0.5, i + 0.5], lw=2, c="w")
        plt.tight_layout()
        self.canvas = FigureCanvas(fig)
        self.layout().addWidget(self.canvas)


class NetworkConfiguration(QtWidgets.QWidget):

    def __init__(self, connections, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections_ = connections
        self.names = list(self.connections_.keys())
        self.setLayout(QtWidgets.QHBoxLayout())
        # Get all ports from connections
        self.broadcast_ports = sorted({d.get("port", "") for d in self.connections_.values()})
        self.receiver_ports = sorted({d.get("receiver", "") for d in self.connections_.values()})
        self.sender_ports = sorted({d.get("sender", "") for d in self.connections_.values()})
        # Create PUB/SUB connectivity matrix
        self.M = np.zeros((len(self.names), len(self.names)), dtype="uint8")
        for i, name in enumerate(self.names):
            subs = [vals[0] for vals in self.connections_[name].get("subscriptions", [])]
            js = [self.names.index(sub) for sub in subs]
            self.M[i, js] = 1
        self.connectivity_widget = ConnectivityWidget(self.M, self.names)
        # Create widgets for each port type
        self.broadcast_widget = ItemAssignmentWidget("Ports", self.broadcast_ports)
        self.senders_widget = ItemAssignmentWidget("Outputs", self.sender_ports)
        self.receivers_widget = ItemAssignmentWidget("Inputs", self.receiver_ports)
        # Add ports to widgets
        for name, connections in self.connections_.items():
            self.broadcast_widget.addRow(name, connections.get("port", ""))
            self.senders_widget.addRow(name, connections.get("sender", ""))
            self.receivers_widget.addRow(name, connections.get("receiver", ""))
        # Create tabs
        self.broadcast_tab = QtWidgets.QWidget()
        self.broadcast_tab.setLayout(QtWidgets.QHBoxLayout())
        self.broadcast_tab.layout().addWidget(self.broadcast_widget)
        self.broadcast_tab.layout().addWidget(self.connectivity_widget)
        self.communications_tab = QtWidgets.QWidget()
        self.communications_tab.setLayout(QtWidgets.QHBoxLayout())
        self.communications_tab.layout().addWidget(self.senders_widget)
        self.communications_tab.layout().addWidget(self.receivers_widget)
        # Add tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.broadcast_tab, "Broadcasting")
        self.tabs.addTab(self.communications_tab, "Communication")
        self.layout().addWidget(self.tabs)

    @property
    def connections(self) -> dict:
        connections = self.connections_.copy()
        for name in self.names:
            port = self.broadcast_widget.getValue(name)
            if port:
                # UPDATE PUBLISHER
                connections[name]["publisher"] = port.replace("localhost", "*")
                # UPDATE SUBSCRIPTIONS
                for worker, d in connections.items():
                    subs = d.get("subscriptions")
                    if subs:
                        for i, sub in enumerate(subs):
                            if sub[0] == name:
                                d["subscriptions"][i] = (sub[0], port, sub[2])
            sender = self.senders_widget.getValue(name)
            if sender:
                connections[name]["sender"] = sender
            receiver = self.receivers_widget.getValue(name)
            if receiver:
                connections[name]["receiver"] = receiver
        return connections

    @staticmethod
    def run(connections):
        app = QtWidgets.QApplication([])
        win = NetworkConfiguration(connections)
        win.show()
        app.exec_()
        return win.connections
