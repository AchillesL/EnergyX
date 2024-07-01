from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox


class ClearableDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.setValue(0.0)
            self.clear()

        else:
            super().keyPressEvent(event)


class ClearableSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            self.setValue(0)
            self.clear()
        else:
            super().keyPressEvent(event)