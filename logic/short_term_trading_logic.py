import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QAbstractListModel, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QDialog, QCompleter

from database.db_helper import DBHelper
from ui.short_term_trading import Ui_Dialog
from utils import utils


class ProductModel(QAbstractListModel):
    def __init__(self, products_info, parent=None):
        super().__init__(parent)
        self.products_info = products_info

    def rowCount(self, parent=QModelIndex()):
        return len(self.products_info)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        # 处理显示和编辑角色
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.products_info[index.row()]['name']
        elif role == Qt.UserRole:
            return self.products_info[index.row()]['py']
        return None


# 修改 ProductFilterProxyModel 的 filterAcceptsRow 方法
class ProductFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ''

    def setFilterText(self, text):
        self.filter_text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        # 增加空值匹配逻辑
        if not self.filter_text:
            return True  # 允许显示所有选项当输入为空时

        name = self.sourceModel().index(source_row, 0).data(Qt.DisplayRole).lower()
        py = self.sourceModel().index(source_row, 0).data(Qt.UserRole).lower()
        return self.filter_text in name or py.startswith(self.filter_text)

class ShortTermTradingDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()

        # 初始化基础UI
        self.setupUi(self)
        self._init_window_properties()
        self.db_helper = DBHelper()

        # 初始化组件
        self._init_futures_selector()
        # 初始化价格输入框
        self._clear_price_inputs()

        # 连接信号槽
        self._connect_signals()

        self.doubleSpinBox_price_1.setRange(0, 100000)
        self.doubleSpinBox_price_2.setRange(0, 100000)

    # ----------------------
    # 初始化相关方法
    # ----------------------
    def _init_window_properties(self):
        """设置窗口基本属性"""
        self.setWindowTitle("OnePercentAlpha (短线交易)")
        self.setWindowIcon(QIcon(utils.get_resource_path('pic\energy.ico')))
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowStaysOnTopHint |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowCloseButtonHint)

    def _init_futures_selector(self):
        self.futures_products = self.db_helper.get_all_futures_products()

        # 确保pin_yin字段格式为带空格的全拼（如"ping guo"）
        self.products_info = [
            {'name': p.trading_product, 'py': p.pin_yin}
            for p in self.futures_products
        ]

        # 创建数据模型
        self.products_info = [
            {'name': p.trading_product, 'py': p.pin_yin}
            for p in self.futures_products
        ]

        # 创建模型体系
        self.product_model = ProductModel(self.products_info)
        self.proxy_model = ProductFilterProxyModel()
        self.proxy_model.setSourceModel(self.product_model)

        # 设置ComboBox模型（关键修改）
        self.comboBox_futures_type.setModel(self.proxy_model)
        self.comboBox_futures_type.setModelColumn(0)  # 显示name列

        self._setup_completer()
        self.comboBox_futures_type.setCurrentIndex(-1)

    # 修改 ShortTermTradingDialog 的 _setup_completer 方法
    def _setup_completer(self):
        self.completer = QCompleter(self)
        self.completer.setModel(self.proxy_model)
        self.completer.setCaseSensitivity(False)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        # 连接激活信号
        self.completer.activated.connect(self._handle_completer_selection)

        self.comboBox_futures_type.setEditable(True)
        self.comboBox_futures_type.setCompleter(self.completer)

        # 修正信号连接名称：把 _update_filter 改为 _update_completer_filter
        self.comboBox_futures_type.lineEdit().textEdited.connect(self._update_completer_filter)

    def _update_completer_filter(self, text):
        """更新过滤条件"""
        self.proxy_model.setFilterText(text)
        # 强制清除当前选择状态
        self.comboBox_futures_type.setCurrentIndex(-1)
        self.comboBox_futures_type.lineEdit().setText(text)  # 确保显示当前输入内容


    def _handle_completer_selection(self, index):
        """处理补全项选择"""
        # 通过代理模型获取源模型索引
        source_index = self.proxy_model.mapToSource(index)
        # 设置当前索引并更新显示
        self.comboBox_futures_type.setCurrentIndex(
            self.proxy_model.mapFromSource(source_index).row()
        )

    def _on_completer_activated(self, text):
        """ 用户显式选择时更新内容 """
        self.comboBox_futures_type.lineEdit().setText(text)
        self.comboBox_futures_type.setCurrentText(text)

    def _handle_completer_selection(self, text):
        """当用户从补全列表中选择时，手动更新编辑框内容"""
        self.comboBox_futures_type.lineEdit().setText(text)

    def _update_completer_filter(self, text):
        """更新过滤条件并打印调试信息"""
        print(f"\n[DEBUG] 输入内容: {text}")
        self.proxy_model.setFilterText(text)

        # 打印当前可见项
        visible_items = [
            self.proxy_model.index(i, 0).data()
            for i in range(self.proxy_model.rowCount())
        ]
        print(f"[DEBUG] 过滤结果: {visible_items}")

    def _clear_price_inputs(self):
        """清空价格输入框"""
        self.doubleSpinBox_price_1.clear()
        self.doubleSpinBox_price_2.clear()

    # ----------------------
    # 信号连接
    # ----------------------
    def _connect_signals(self):
        """连接所有信号与槽"""
        self.comboBox_futures_type.currentTextChanged.connect(self._handle_text_changed)
        self.doubleSpinBox_price_1.valueChanged.connect(self._calculate_position)
        self.doubleSpinBox_price_2.valueChanged.connect(self._calculate_position)

    def _handle_text_changed(self, text):
        """处理文本变化事件"""
        self._update_text_style(text)
        self._process_selection(text)

    # ----------------------
    # UI更新方法
    # ----------------------
    def _update_text_style(self, text):
        """更新输入框文本样式"""
        font = QFont()
        palette = self.comboBox_futures_type.lineEdit().palette()

        if text in self.products_info:
            font.setBold(True)
            palette.setColor(QPalette.Text, QColor("red"))
        else:
            font.setBold(False)
            palette.setColor(QPalette.Text, QColor("black"))

        self.comboBox_futures_type.lineEdit().setFont(font)
        self.comboBox_futures_type.lineEdit().setPalette(palette)

    # ----------------------
    # 业务逻辑
    # ----------------------
    def _process_selection(self, text):
        self.print_selected_text(text)
        # 检查是否存在匹配的产品名称
        if any(p['name'] == text for p in self.products_info):
            self.selected_future = self._get_selected_future(text)
            self._on_future_changed()

    def _on_future_changed(self):
        """当期货品种变化时的业务处理"""
        self._setup_price_inputs()
        self.textBrowser.clear()

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

    # ----------------------
    # 辅助方法
    # ----------------------
    def _get_selected_future(self, text):
        """根据文本获取期货对象"""
        return next((p for p in self.futures_products if p.trading_product == text), None)

    @staticmethod
    def print_selected_text(text):
        """调试用打印方法"""
        print(f"Selected text: {text}")

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
