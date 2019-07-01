from PyQt5.QtWidgets import QFrame


class HorizontalLine(QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(self.HLine | self.Plain)


class VerticalLine(QFrame):

    def __init__(self):
        super().__init__()
        self.setFrameStyle(self.VLine | self.Plain)
