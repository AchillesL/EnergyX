import ctypes

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtWidgets import QDialog

from database.db_helper import DBHelper
from database.models import FuturesPositionBean
from ui.add_position_py import Ui_Dialog
from utils import utils


class AddPositionDialog(QDialog, Ui_Dialog):

    position_saved = pyqtSignal()  # 定义一个信号

    def __init__(self, parent=None, position: FuturesPositionBean =None):
        super().__init__(parent)

        self.position = position

        self.setupUi(self)

        self.initDB()
        self.initUI()

        self.setWindowTitle("Zengguo.Liang")

        self.setWindowFlags(
            self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint)

    def initDB(self):
        self.db_helper = DBHelper()
        self.futures_products = self.db_helper.get_all_futures_products()
        self.selected_future = self.get_selected_future_by_text(self.position.product_name)

    def initUI(self):
        self.comboBox_futures_type.setEditable(True)
        self.comboBox_futures_type.setEditText(self.position.product_name)
        palette = self.comboBox_futures_type.lineEdit().palette()
        palette.setColor(QPalette.Text, QColor("red"))
        self.comboBox_futures_type.lineEdit().setPalette(palette)
        self.comboBox_futures_type.setEnabled(False)

        if self.position.operation_direction == 1:
            self.radioButton_long.setChecked(True)
            self.radioButton_short.setChecked(False)
        else:
            self.radioButton_long.setChecked(False)
            self.radioButton_short.setChecked(True)

        self.radioButton_long.setChecked(False)
        self.radioButton_short.setEnabled(False)

        self.doubleSpinBox_new_stop_loss_price.clear()
        self.spinBox_add_position_quantity.clear()
        self.doubleSpinBox_add_pos_price.clear()

        self.doubleSpinBox_new_stop_loss_price.setRange(0, 100000000)
        self.spinBox_add_position_quantity.setRange(-1 * self.position.position_quantity, 100000000)
        self.doubleSpinBox_add_pos_price.setRange(0, 100000000)

        self.doubleSpinBox_new_stop_loss_price.valueChanged.connect(self.calculate)
        self.spinBox_add_position_quantity.valueChanged.connect(self.calculate)
        self.doubleSpinBox_add_pos_price.valueChanged.connect(self.calculate)

        self.doubleSpinBox_new_stop_loss_price.setSingleStep(self.selected_future.minimum_price_change)
        self.spinBox_add_position_quantity.setSingleStep(1)
        self.doubleSpinBox_add_pos_price.setSingleStep(self.selected_future.minimum_price_change)

        self.doubleSpinBox_new_stop_loss_price.installEventFilter(self)
        self.spinBox_add_position_quantity.installEventFilter(self)
        self.doubleSpinBox_add_pos_price.installEventFilter(self)

        self.pushButton_save.clicked.connect(self.save_position)
        self.pushButton_clear.clicked.connect(self.clear_position)

        self.calculation_results = {}

    def get_selected_future_by_text(self, text):
        for product in self.futures_products:
            if text == product.trading_product:
                return product

    def calculate(self):
        if not self.doubleSpinBox_new_stop_loss_price.lineEdit().text() or not self.spinBox_add_position_quantity.lineEdit().text() or not self.doubleSpinBox_add_pos_price.lineEdit().text():
            return

        position_factor = 1 if self.radioButton_long.isChecked() else -1

        # 计算旧止损金额
        old_stop_loss_amount = (self.position.stop_loss_price - self.position.cost_price) * self.position.position_quantity * self.selected_future.trading_units * position_factor
        old_position_value = self.position.cost_price * self.position.position_quantity * self.selected_future.trading_units

        # 计算新头寸数量
        add_pos_quantity = self.spinBox_add_position_quantity.value()
        new_pos_quantity = int(self.position.position_quantity + add_pos_quantity)

        if new_pos_quantity == 0:
            new_cost_price = 0
            new_stop_loss_amount = 0
            new_position_value = 0
            cost_price_str = "N/A"  # 表示无法计算
            stop_loss_amount_str = "N/A"
            position_value_str = "N/A"
        else:
            new_cost_price = (self.position.cost_price * self.position.position_quantity + self.doubleSpinBox_add_pos_price.value() * add_pos_quantity) / new_pos_quantity
            new_stop_loss_amount = (self.doubleSpinBox_new_stop_loss_price.value() - new_cost_price) * new_pos_quantity * self.selected_future.trading_units * position_factor
            new_position_value = new_cost_price * new_pos_quantity * self.selected_future.trading_units
            cost_price_str = utils.format_to_two_places(new_cost_price)
            stop_loss_amount_str = utils.format_to_two_places(new_stop_loss_amount)
            position_value_str = utils.format_to_integer(new_position_value)

        self.calculation_results = {
            'new_stop_loss_price': self.doubleSpinBox_new_stop_loss_price.value(),
            'new_position_quantity': new_pos_quantity,
            'old_stop_loss_amount': old_stop_loss_amount,
            'new_stop_loss_amount': new_stop_loss_amount,
            'old_position_value': old_position_value,
            'new_position_value': new_position_value,
            'old_cost_price': self.position.cost_price,
            'new_cost_price': new_cost_price,
            'cost_price_str': cost_price_str,
            'stop_loss_amount_str': stop_loss_amount_str,
            'position_value_str': position_value_str,
        }

        self.display_calculation()

    def display_calculation(self):
        result = self.calculation_results

        self.textBrowser.setText(
            "1.止损金额: {} -> {};\n"
            "2.头寸价值: {} -> {};\n"
            "3.新成本价: {} -> {};\n".format(
                utils.format_to_two_places(result['old_stop_loss_amount']),
                result['stop_loss_amount_str'],
                utils.format_to_integer(result['old_position_value']),
                result['position_value_str'],
                utils.format_to_two_places(result['old_cost_price']),
                result['cost_price_str']
            )
        )

    def save_position(self):
        result = self.calculation_results
        if not result:
            return

        self.position.position_quantity = result['new_position_quantity']
        self.position.profit_loss_amount = result['new_stop_loss_amount']
        self.position.cost_price = result['new_cost_price']
        self.position.stop_loss_price = result['new_stop_loss_price']
        self.position.product_value = result['new_position_value']

        self.db_helper.update_futures_position(self.position)
        self.position_saved.emit()
        self.close()


    def clear_position(self):
        self.doubleSpinBox_new_stop_loss_price.clear()
        self.spinBox_add_position_quantity.clear()
        self.doubleSpinBox_add_pos_price.clear()
        self.textBrowser.clear()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.FocusIn:
            if obj in (self.doubleSpinBox_new_stop_loss_price, self.spinBox_add_position_quantity,
                       self.doubleSpinBox_add_pos_price):
                utils.set_num_lock(True)
        return super().eventFilter(obj, event)
