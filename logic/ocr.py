import sys
import easyocr
import numpy as np
from PIL import ImageGrab
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QDialog, QTextEdit
from abc import ABC, abstractmethod
import utils.utils

class TextRecognitionListener(ABC):
    @abstractmethod
    def on_text_recognized(self, text: str, is_number: bool):
        pass

class TransparentWindow(QDialog):
    def __init__(self, listener=None):
        super().__init__()
        self.listener = listener
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PyQt5 Window with Screenshot Background')
        self.showFullScreen()
        self.setWindowOpacity(0.5)
        self.rect = QRect()
        self.drawing = False
        self.start = None
        self.end = None

    def add_listener(self, listener):
        self.listener = listener

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # 清空绘制区域并隐藏窗口
            self.rect = QRect()
            self.update()
            self.hide()
            # 通知监听器
            if self.listener:
                self.listener.on_text_recognized("None", False)
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start = event.pos()
            self.drawing = True
            QApplication.setOverrideCursor(Qt.CrossCursor)

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end = event.pos()
            self.rect = QRect(self.start, self.end).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.record_rectangle()
            QApplication.restoreOverrideCursor()

    def record_rectangle(self):
        x = self.rect.x()
        y = self.rect.y()
        width = self.rect.width()
        height = self.rect.height()
        print(f'Rectangle - x: {x}, y: {y}, width: {width}, height: {height}')

        self.rect = QRect()
        self.hide()
        self.update()

        bbox = (x, y, x + width, y + height)
        im = ImageGrab.grab(bbox=bbox)
        im_np = np.array(im)

        reader = easyocr.Reader(['en'], gpu=True)
        result = reader.readtext(im_np)

        texts = [text for (bbox, text, prob) in result]
        full_text = ' '.join(texts)
        is_num = utils.utils.is_number(full_text)

        if self.listener:
            self.listener.on_text_recognized(full_text, is_num)

    def paintEvent(self, event):
        if not self.rect.isNull():
            painter = QPainter(self)
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)
            painter.drawRect(self.rect)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    class MyListener(TextRecognitionListener):
        def on_text_recognized(self, text: str, is_number: bool):
            print(f"Received text: {text}, is_number: {is_number}")

    window = TransparentWindow()
    window.add_listener(MyListener())

    window.show()
    sys.exit(app.exec_())
