import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from logic.main_dialog_logic import MainDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainDialog()
    window.show()
    sys.exit(app.exec_())
