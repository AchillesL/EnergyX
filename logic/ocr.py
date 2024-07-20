import sys
import easyocr
import numpy as np
from PIL import ImageGrab
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QDialog, QTextEdit

import utils.utils

class TransparentWindow(QDialog):
    def __init__(self, ocr_show_widget):
        super().__init__()
        self.ocr_show_widget = ocr_show_widget
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PyQt5 Window with Screenshot Background')

        # 设置窗口全屏
        self.showFullScreen()

        # 设置窗口的透明度
        self.setWindowOpacity(0.5)

        # 初始化绘制矩形相关的变量
        self.rect = QRect()
        self.drawing = False
        self.start = None
        self.end = None

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
        # 记录矩形框的坐标和大小
        x = self.rect.x()
        y = self.rect.y()
        width = self.rect.width()
        height = self.rect.height()
        print(f'Rectangle - x: {x}, y: {y}, width: {width}, height: {height}')

        self.close()
        bbox = (x, y, x + width, y + height)
        im = ImageGrab.grab(bbox=bbox)

        # 转换为NumPy数组
        im_np = np.array(im)

        # 使用easyocr识别截图中的文本
        reader = easyocr.Reader(['en', 'ch_sim'], gpu=True)  # 指定语言为英语，可以根据需要修改
        result = reader.readtext(im_np)

        # 打印识别到的文本
        for (bbox, text, prob) in result:
            print(f'Text: {text}, Probability: {prob}')

        texts = [text for (bbox, text, prob) in result]
        full_text = ' '.join(texts)

        if utils.utils.is_number(full_text):
            self.ocr_show_widget.setValue(float(full_text))

            line_edit = self.ocr_show_widget.lineEdit()
            text_length = len(line_edit.text())
            line_edit.setCursorPosition(text_length)

    def paintEvent(self, event):
        if not self.rect.isNull():
            painter = QPainter(self)
            pen = QPen(QColor(255, 0, 0), 2)
            painter.setPen(pen)
            painter.drawRect(self.rect)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ocr_show_widget = QTextEdit()  # 创建一个示例的 ocr_show_widget
    window = TransparentWindow(ocr_show_widget)
    window.show()
    sys.exit(app.exec_())
