import sys

import pyautogui
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QDialog

from ui.ths_helper import Ui_Dialog


class MainWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setStyleSheet("""
                QDialog {
                    border: 0.5px solid black;
                }
            """)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # ===== 鼠标拖动相关变量 =====
        self.drag_pos = QPoint()

        # ===== 绑定所有按钮事件 =====
        self.ui.pushButton_ChatInvert.clicked.connect(self.reverse_chart)
        self.ui.pushButton_PageUp.clicked.connect(self.page_up)
        self.ui.pushButton_PageDown.clicked.connect(self.page_down)
        self.ui.pushButton_close.clicked.connect(self.close_app)
        self.ui.pushButton_pankou.clicked.connect(self.pankou)

    def adjustWindowPosition(self):
        """ 将窗口左侧对齐屏幕垂直中线 """
        # 获取屏幕参数
        screen = QApplication.primaryScreen().availableGeometry()

        # 计算中线坐标
        vertical_center_x = screen.width() // 2

        # 设置窗口位置（左侧贴垂直中线，顶部贴边）
        self.move(vertical_center_x, 0)


    # ===== 鼠标事件处理 =====
    def mousePressEvent(self, event):
        """ 记录拖动起始位置 """
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """ 实现窗口拖动 """
        if event.buttons() == Qt.LeftButton:
            # 只在鼠标位于空白区域时拖动
            if not (self.ui.pushButton_ChatInvert.underMouse() or
                    self.ui.pushButton_PageUp.underMouse() or
                    self.ui.pushButton_PageDown.underMouse() or
                    self.ui.pushButton_close.underMouse()):
                self.move(event.globalPos() - self.drag_pos)
                event.accept()

    # ===== 功能方法 =====
    def _activate_win(self):
        """ 通用窗口激活逻辑 """
        import pygetwindow as gw
        win = gw.getWindowsWithTitle("同花顺期货通")[0]
        win.activate()

    def reverse_chart(self):
        try:
            self._activate_win()
            pyautogui.hotkey('ctrl', 'alt', 'f')
        except Exception as e:
            print(f"反转错误: {str(e)}")

    def page_up(self):
        try:
            self._activate_win()
            pyautogui.press('pageup')
        except Exception as e:
            print(f"翻页上错误: {str(e)}")

    def page_down(self):
        try:
            self._activate_win()
            pyautogui.press('pagedown')
        except Exception as e:
            print(f"翻页下错误: {str(e)}")

    def pankou(self):
        try:
            self._activate_win()
            pyautogui.hotkey('ctrl', 'l')
        except Exception as e:
            print(f"翻页下错误: {str(e)}")

    def close_app(self):
        self.close()

    def showEvent(self, event):
        self.adjustWindowPosition()
        super().showEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    sys.exit(app.exec_())
