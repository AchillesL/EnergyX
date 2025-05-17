import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QDialog

from database.db_helper import DBHelper
from ui.short_term_trading import Ui_Dialog
from utils import utils
from utils.smart_combo_box import SmartComboBox


class ShortTermTradingDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()

        # 初始化基础UI
        self.setupUi(self)

        self.comboBox_futures_type = SmartComboBox.replace_existing_combobox(
            old_combobox=self.comboBox_futures_type,
            parent_layout=self.gridLayout
        )

        self.setWindowTitle("OnePercentAlpha (短线交易)")
        self.setWindowIcon(QIcon(utils.get_resource_path('pic\energy.ico')))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.db_helper = DBHelper()
        self.initialize_futures_type_view()

        self._clear_price_inputs()
        self.doubleSpinBox_price_1.setRange(0, 100000)
        self.doubleSpinBox_price_2.setRange(0, 100000)

        self.comboBox_futures_type.currentTextChanged.connect(self.handle_text_changed)
        self.doubleSpinBox_price_1.valueChanged.connect(self._calculate_position)
        self.doubleSpinBox_price_2.valueChanged.connect(self._calculate_position)

    def initialize_futures_type_view(self):
        self.futures_products = self.db_helper.get_all_futures_products()
        model = QStandardItemModel()
        for product in self.futures_products:
            item = QStandardItem(product.trading_product)
            item.setData(product.pin_yin, Qt.UserRole)
            model.appendRow(item)
        self.comboBox_futures_type.setModel(model)
        self.comboBox_futures_type.setCurrentIndex(-1)

    def handle_text_changed(self, text):
        model = self.comboBox_futures_type.model()
        exists = any(model.item(i).text() == text for i in range(model.rowCount()))

        font = QFont()
        palette = self.comboBox_futures_type.lineEdit().palette()

        if exists:
            self.selected_future = self.get_selected_future_by_text(text)
            self.select_future_changed()
            font.setBold(True)
            palette.setColor(QPalette.Text, QColor("red"))
        else:
            font.setBold(False)
            palette.setColor(QPalette.Text, QColor("black"))

        self.comboBox_futures_type.lineEdit().setFont(font)
        self.comboBox_futures_type.lineEdit().setPalette(palette)

    def get_selected_future_by_text(self, text):
        for product in self.futures_products:
            if text == product.trading_product:
                return product


    def select_future_changed(self):
        self._setup_price_inputs()
        self.textBrowser.clear()

    def _clear_price_inputs(self):
        """清空价格输入框"""
        self.doubleSpinBox_price_1.clear()
        self.doubleSpinBox_price_2.clear()

    def _setup_price_inputs(self):
        """配置价格输入框参数"""
        if not self.selected_future:
            return

        # 获取最小价格变动和计算小数位数
        step_value = self.selected_future.minimum_price_change
        decimal_places = self._get_decimal_places(step_value)

        # 配置每个输入框
        for spinner in [self.doubleSpinBox_price_1, self.doubleSpinBox_price_2]:
            spinner.setDecimals(decimal_places)  # 设置小数位数
            spinner.setSingleStep(step_value)  # 设置步长
            spinner.setValue(0)  # 重置值
            spinner.clear()

    def _get_decimal_places(self, value):
        """智能计算需要显示的小数位数"""
        if isinstance(value, int) or value.is_integer():
            return 0

        # 处理浮点数精度问题
        str_value = "{:.10f}".format(value).rstrip('0').rstrip('.')

        if '.' in str_value:
            return len(str_value.split('.')[1])
        return 0

    def _calculate_position(self):
        """计算可开仓手数和风险比例"""
        if not self._validate_inputs():
            self.textBrowser.clear()
            # 使用行高和min-height双重保障
            error_html = '''
            <div style="
                margin-top:1em !important;
                line-height:1.2;
                min-height:2em;
                display:block;
            ">计算出现错误，请检查输入参数</div>
            '''
            self.textBrowser.setHtml(error_html)
            return

        try:
            account = self.db_helper.get_account_bean()
            price_diff, _ = self._get_price_params()
            trading_units = self.selected_future.trading_units
            min_change = self.selected_future.minimum_price_change
            loss_per_lot = (price_diff + min_change) * trading_units
            equity = account.dynamic_equity
            max_lots = self._calculate_max_lots(equity, loss_per_lot)
            # 计算止损金额
            current_stop_loss = max_lots * loss_per_lot
            over_stop_loss = (max_lots + 1) * loss_per_lot
            # 计算风险比例
            actual_risk = (current_stop_loss / equity * 100) if equity > 0 else 0
            over_risk = None
            # 计算超出手数的风险
            if max_lots >= 1:
                over_risk = (over_stop_loss / equity * 100) if equity > 0 else 0
            result = self._format_result(
                max_lots,
                actual_risk,
                over_risk,
                current_stop_loss,
                over_stop_loss
            )
            self.textBrowser.setHtml(result)
        except Exception as e:
            print(f"计算错误: {str(e)}")
            self.textBrowser.setText("计算出现错误，请检查输入参数")

    def _validate_inputs(self):
        """验证输入有效性"""
        conditions = [
            self.selected_future is not None,
            self.doubleSpinBox_price_1.value() > 0,
            self.doubleSpinBox_price_2.value() > 0,
            self.doubleSpinBox_price_1.value() != self.doubleSpinBox_price_2.value(),
            self.db_helper.get_account_bean() is not None,
            self.db_helper.get_account_bean().dynamic_equity > 0
        ]
        return all(conditions)

    def _get_price_params(self):
        """获取价格相关参数"""
        price1 = self.doubleSpinBox_price_1.value()
        price2 = self.doubleSpinBox_price_2.value()
        return abs(price1 - price2), min(price1, price2)  # 取较小值作为止损价

    def _calculate_max_lots(self, equity, loss_per_lot):
        """计算最大可开仓手数"""
        if loss_per_lot <= 0:
            return 0
        return int((equity * 0.005) // loss_per_lot)

    def _format_result(self, lots, actual_risk, over_risk, current_stop_loss, over_stop_loss):
        STYLE_RED_BOLD = "<span style='color:#FF0000; font-weight:600;'>%s</span>"

        # 使用绝对像素值确保一致性
        MARGIN_FIRST = "style='margin:16px 0 8px 0 !important; display: block;'"  # 假设1em=16px
        MARGIN_SECOND = "style='margin:12px 0 8px 0 !important; display: block;'"  # 0.8em≈12px

        lines = [
            f"<div {MARGIN_FIRST}>"
            f"1.可开手数: {STYLE_RED_BOLD % lots} 手，"
            f"止损金额：{STYLE_RED_BOLD % f'{current_stop_loss:.2f}'} 元，"
            f"风险比例：{STYLE_RED_BOLD % f'{actual_risk:.2f}%'};"
            "</div>"
        ]
        if over_risk is not None:
            lines.append(
                f"<div {MARGIN_SECOND}>"
                f"2.超开1手时，"
                f"止损金额：{STYLE_RED_BOLD % f'{over_stop_loss:.2f}'} 元，"
                f"风险比例：{STYLE_RED_BOLD % f'{over_risk:.3f}%'};"
                "</div>"
            )
        return f"<div style='line-height:1; padding:0 !important;'>{''.join(lines)}</div>"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShortTermTradingDialog()
    window.show()
    sys.exit(app.exec_())
