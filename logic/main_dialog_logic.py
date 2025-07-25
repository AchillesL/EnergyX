import pygame
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QTime, QTimer, QDate
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QCompleter, QTableWidgetItem, QMenu, QLabel, QWidgetAction, QWidget, \
    QVBoxLayout, QTableWidget, QLCDNumber

from database.db_helper import DBHelper
from database.models import FuturesPositionBean
from logic import ths_helper_logic
from logic.add_position_logic import AddPositionDialog
from logic.reminder_dialog_logic import ReminderDialog
from logic.short_term_trading_logic import ShortTermTradingDialog
from ui.main_dialog_ui import Ui_Dialog
# from ui.ocr import TransparentWindow
from utils import utils
from utils.futures_product_info_utils import FuturesProductInfoUtils
from utils.smart_combo_box import SmartComboBox


class MainDialog(QMainWindow, Ui_Dialog):
    def __init__(self):
        super().__init__()

        self.resize(750, 500)
        self.setMinimumSize(QtCore.QSize(750, 560))
        self.setMaximumSize(QtCore.QSize(750, 560))

        self.db_helper = DBHelper()
        self.selected_future = None
        self.position_bean = None
        self.previous_focus_widget = None  # 用于记录之前焦点所在的控件
        self.is_maximized = False

        self.setupUi(self)

        self.initDB()
        self.initUI()
        self.original_width = self.width()

    def initUI(self):

        # 设置窗口标题和图标
        self.setWindowTitle("OnePercentAlpha")

        self.setWindowIcon(QIcon(utils.get_resource_path('pic\energy.ico')))

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint)

        # 初始化控件和连接信号
        self.setup_signals()
        self.setup_event_filters()

        self.initialize_futures_type_view()
        self.reset_spin_boxes()

        self.doubleSpinBox_stop_loss_price.setRange(0, 100000000)
        self.doubleSpinBox_cost_price.setRange(0, 100000000)
        self.spinBox_position_quantity.setRange(0, 100000000)
        self.doubleSpinBox_take_profit_price.setRange(0, 100000000)

        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)  # 所有列均匀拉伸
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget.setSelectionMode(QTableWidget.SingleSelection)
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.show_context_menu)

        self.lcdNumber.setNumDigits(8)

        self.lcdNumber.setSegmentStyle(QLCDNumber.Flat)  # 设置段样式为平面样式

        pygame.init()
        pygame.mixer.init()
        # pygame.mixer.music.load("./music/didi.mp3")
        # pygame.mixer.music.load(r"C:\Users\zengg\Documents\Code\PycharmProjects\EnergyX\music\didi.mp3")

        self.update_time()

        # 创建一个定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次

        self.update_account_and_position_info()
        self.helper_dialog = ths_helper_logic.MainWindow()  # 创建对话框实例

    def setup_signals(self):
        self.pushButton_save.clicked.connect(self.on_save_clicked)
        self.pushButton_clear.clicked.connect(self.on_clear_clicked)
        self.pushButton_clear_table.clicked.connect(self.on_clear_all_positions_clicked)
        self.pushButton_account.clicked.connect(self.toggle_width)
        self.pushButton_reminder.clicked.connect(self.on_reminder_clicked)
        self.pushButton_ths_helper.clicked.connect(self.on_ths_helper_clicked)
        self.pushButton_duanxian.clicked.connect(self.on_short_term_trading)
        self.lineEdit_dynamic_equity.returnPressed.connect(self.on_return_pressed_to_dynamic_equity)
        # self.pushButton_ocr.clicked.connect(self.on_ocr_clicked)

        self.doubleSpinBox_stop_loss_price.valueChanged.connect(self.calculate)
        self.doubleSpinBox_cost_price.valueChanged.connect(self.calculate)
        self.spinBox_position_quantity.valueChanged.connect(self.calculate)
        self.doubleSpinBox_take_profit_price.valueChanged.connect(self.calculate)

        self.radioButton_long.toggled.connect(self.radioButtonStateChanged)
        self.radioButton_short.toggled.connect(self.radioButtonStateChanged)

        # 连接cellClicked信号到新槽函数
        self.tableWidget.cellClicked.connect(self.on_table_row_clicked)

    def setup_event_filters(self):
        self.doubleSpinBox_stop_loss_price.installEventFilter(self)
        self.doubleSpinBox_cost_price.installEventFilter(self)
        self.spinBox_position_quantity.installEventFilter(self)
        self.lineEdit_dynamic_equity.installEventFilter(self)
        self.doubleSpinBox_take_profit_price.installEventFilter(self)
        self.radio_event_filter = RadioButtonEventFilter(self.radioButton_long, self.radioButton_short)
        self.radioButton_long.installEventFilter(self.radio_event_filter)
        self.radioButton_short.installEventFilter(self.radio_event_filter)

    def update_time(self):
        current_date = QDate.currentDate()
        day_of_week = current_date.dayOfWeek()  # 获取当前星期几，返回值为1-7, 1为周一，7为周日

        # 判断是否为周六(6)或周日(7)，如果是则返回，不执行提醒
        if day_of_week in (6, 7):
            self.lcdNumber_reminder.display("00:00:00")
            return

        current_time = QTime.currentTime()
        time_str = current_time.toString('hh:mm:ss')
        self.lcdNumber.display(time_str)

        # 获取提醒时间列表
        self.reminder_time_list = self.db_helper.get_reminder_time_list()

        self.target_time = None

        for time_str in self.reminder_time_list:
            target_time = QTime.fromString(time_str, 'hh:mm')
            if target_time.isValid():
                diff = current_time.secsTo(target_time)
                if diff < 0:
                    continue
                else:
                    self.target_time = target_time
                    break

        if self.target_time is not None:
            # 计算两个提醒时间的差值
            reminder_one_diff = current_time.secsTo(self.target_time) - (
                        self.db_helper.load_setting_bean().reminder_one_ahead_of_min * 60 + self.db_helper.load_setting_bean().reminder_one_ahead_of_sec)
            reminder_two_diff = current_time.secsTo(self.target_time) - (
                        self.db_helper.load_setting_bean().reminder_two_ahead_of_min * 60 + self.db_helper.load_setting_bean().reminder_two_ahead_of_sec)

            # 根据哪个提醒时间未触发，选择显示倒计时
            if reminder_one_diff > 0:
                diff = reminder_one_diff
            elif reminder_two_diff > 0:
                diff = reminder_two_diff
            else:
                diff = 0

            # 显示倒计时
            if diff > 0:
                hours, remainder = divmod(diff, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.lcdNumber_reminder.display(f"{hours:02}:{minutes:02}:{seconds:02}")
            else:
                self.lcdNumber_reminder.display("00:00:00")

            # 如果到达第一个提醒时间，播放声音
            if reminder_one_diff == 0:
                self.play_reminder_sound()

            # 如果到达第二个提醒时间，播放声音
            if reminder_two_diff == 0:
                self.play_reminder_sound_2()

        else:
            self.lcdNumber_reminder.display("00:00:00")

    def play_reminder_sound(self):
        pygame.mixer.music.load(utils.get_resource_path("music/didi.mp3"))
        pygame.mixer.music.play()

    def play_reminder_sound_2(self):
        pygame.mixer.music.load(utils.get_resource_path("music/didi2.mp3"))
        pygame.mixer.music.queue(utils.get_resource_path("music/didi2.mp3"))
        pygame.mixer.music.play()

    def initDB(self):
        if self.db_helper.is_futures_products_table_empty():
            self.db_helper.insert_future_list(FuturesProductInfoUtils.future_list)

        if self.db_helper.is_account_table_empty():
            self.db_helper.insert_default_account()

    def initialize_futures_type_view(self):

        self.comboBox_futures_type = SmartComboBox.replace_existing_combobox(
            old_combobox=self.comboBox_futures_type,
            parent_layout=self.gridLayout
        )

        self.futures_products = self.db_helper.get_all_futures_products()
        self.products_list = [product.trading_product for product in self.futures_products]

        model = QStandardItemModel()
        for product in self.futures_products:
            item = QStandardItem(product.trading_product)
            item.setData(product.pin_yin, Qt.UserRole)
            model.appendRow(item)
        self.comboBox_futures_type.setModel(model)
        self.comboBox_futures_type.setCurrentIndex(-1)

        self.comboBox_futures_type.currentTextChanged.connect(self.handle_text_changed)

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

    def print_selected_text(self, text):
        print(f"Selected text: {text}")

    def setup_double_spin_boxes(self):
        if self.selected_future is None:
            step_value = 1
            decimals = 0
        else:
            step_value = self.selected_future.minimum_price_change
            # 判断是否为整数
            if step_value == int(step_value):
                decimals = 0
                step_value = int(step_value)  # 确保步长为整数类型
            else:
                # 计算小数位数
                step_str = f"{step_value:.10f}".rstrip('0').rstrip('.')
                decimals = len(step_str.split('.')[1]) if '.' in step_str else 0

        # 设置所有价格输入框的属性
        for spin_box in [
            self.doubleSpinBox_stop_loss_price,
            self.doubleSpinBox_cost_price,
            self.doubleSpinBox_take_profit_price
        ]:
            spin_box.setDecimals(decimals)  # 设置小数位数
            spin_box.setSingleStep(step_value)  # 设置步长
            spin_box.setProperty("minStep", step_value)  # 保存最小步长属性

        self.reset_spin_boxes()

    def reset_spin_boxes(self):
        self.doubleSpinBox_cost_price.setValue(0.0)
        self.doubleSpinBox_stop_loss_price.setValue(0.0)
        self.spinBox_position_quantity.setValue(0)
        self.doubleSpinBox_take_profit_price.setValue(0.0)

        self.doubleSpinBox_cost_price.clear()
        self.doubleSpinBox_stop_loss_price.clear()
        self.spinBox_position_quantity.clear()
        self.doubleSpinBox_take_profit_price.clear()

    def select_future_changed(self):
        self.setup_double_spin_boxes()
        self.textBrowser.clear()

    def radioButtonStateChanged(self):
        if self.radioButton_long.isChecked():
            print("Long position selected")
        elif self.radioButton_short.isChecked():
            print("Short position selected")
        self.calculate()

    def on_save_clicked(self):

        if self.selected_future is None:
            return

        # if self.selected_future is None or not self.doubleSpinBox_stop_loss_price.lineEdit().text() or not self.doubleSpinBox_cost_price.lineEdit().text() or not self.spinBox_position_quantity.lineEdit().text():
        #     return

        cost_price = self.doubleSpinBox_cost_price.value()
        stop_loss_price = self.doubleSpinBox_stop_loss_price.value()
        position_quantity = self.spinBox_position_quantity.value()
        operation_direction = 1 if self.radioButton_long.isChecked() else -1
        profit_loss_amount = (stop_loss_price - cost_price) * position_quantity * self.selected_future.trading_units * operation_direction

        if self.position_bean is None:
            self.position_bean = FuturesPositionBean()
            self.position_bean.product_name = self.selected_future.trading_product
            self.position_bean.initial_stop_loss = profit_loss_amount

        else:
            self.comboBox_futures_type.setEnabled(True)
            self.radioButton_long.setEnabled(True)
            self.radioButton_short.setEnabled(True)

        self.position_bean.operation_direction = operation_direction
        self.position_bean.stop_loss_price = stop_loss_price
        self.position_bean.cost_price = cost_price
        self.position_bean.position_quantity = position_quantity
        self.position_bean.profit_loss_amount = profit_loss_amount
        self.position_bean.product_value = cost_price * position_quantity * self.selected_future.trading_units
        self.position_bean.stop_loss_point = abs(cost_price - stop_loss_price)

        self.db_helper.add_futures_position(self.position_bean)
        self.reset_input_info()
        self.update_account_and_position_info()

    def reset_input_info(self):
        self.reset_spin_boxes()
        self.comboBox_futures_type.setCurrentIndex(-1)
        self.textBrowser.clear()
        self.selected_future = None
        self.position_bean = None

    def on_clear_clicked(self):
        self.reset_input_info()

        self.comboBox_futures_type.setEnabled(True)
        self.radioButton_long.setEnabled(True)
        self.radioButton_short.setEnabled(True)

    def on_clear_all_positions_clicked(self):
        self.db_helper.delete_all_futures_position()
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.update_account_info()

        self.comboBox_futures_type.setEnabled(True)
        self.radioButton_long.setEnabled(True)
        self.radioButton_short.setEnabled(True)

        self.on_clear_clicked()

    def load_all_futures_position_to_table(self):
        self.positions = self.db_helper.load_all_futures_position()
        self.tableWidget.setRowCount(len(self.positions))

        for row, position in enumerate(self.positions):
            # 检查头寸数量是否为0
            if position.position_quantity == 0:
                # 品种名称 (列0)
                self.set_table_item(row, 0, position.product_name)
                # 止损价格 (列1)
                self.set_table_item(row, 1, str(utils.format_to_two_places(position.stop_loss_price)))
                # 其他列显示"——"
                for col in [2, 3, 4, 5, 6, 7]:
                    self.set_table_item(row, col, "—")
            else:
                # 正常处理所有列
                operation_direction_text = "多" if position.operation_direction == 1 else "空"

                self.set_table_item(row, 0, position.product_name)
                self.set_table_item(row, 1, str(utils.format_to_two_places(position.stop_loss_price)))
                self.set_table_item(row, 2, str(utils.format_to_two_places(position.profit_loss_amount)), is_profit_loss=True)
                self.set_table_item(row, 3, str(position.position_quantity))
                self.set_table_item(row, 4, str(utils.format_to_two_places(position.cost_price)))
                self.set_table_item(row, 5, str(utils.format_to_two_places(position.stop_loss_point)))
                self.set_table_item(row, 6, operation_direction_text)
                self.set_table_item(row, 7, str(utils.format_currency(position.product_value)))

    def set_table_item(self, row, column, text, is_profit_loss=False):
        item = QTableWidgetItem(text)
        font = QFont("宋体", 11)
        item.setFont(font)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设置为不可编辑

        if is_profit_loss:
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QColor('red') if float(text) > 0 else QColor('blue'))

        self.tableWidget.setItem(row, column, item)

    def update_account_info(self):
        account_bean = self.db_helper.get_account_bean()
        dynamic_equity = static_equity = account_bean.dynamic_equity

        current_product_value = 0
        used_risk_amount = 0

        futures_position_list = self.db_helper.load_all_futures_position()
        for position in futures_position_list:
            static_equity += position.profit_loss_amount
            current_product_value += position.product_value

            if position.profit_loss_amount < 0:
                used_risk_amount += position.profit_loss_amount * -1

        self.lineEdit_dynamic_equity.setText(str(utils.format_to_integer(dynamic_equity)))
        self.lineEdit_risk_equity.setText(utils.format_currency(str(utils.format_to_integer(static_equity))))
        self.lineEdit_position_value.setText(utils.format_currency(str(utils.format_to_integer(current_product_value))))

        risk_percentage = "INF" if dynamic_equity == 0 else f"{utils.format_to_two_places(used_risk_amount / dynamic_equity * 100):.3f}%"
        self.lineEdit_risk_ratio.setText(f"{utils.format_to_integer(used_risk_amount)}/{risk_percentage}")

    def on_return_pressed_to_dynamic_equity(self):
        account_bean = self.db_helper.get_account_bean()
        account_bean.dynamic_equity = int(self.lineEdit_dynamic_equity.text())
        self.db_helper.update_account_bean(account_bean)
        self.update_account_info()

    def toggle_width(self):
        if self.is_maximized:
            self.setMinimumWidth(self.original_width)
            self.setMaximumWidth(self.original_width)
            self.pushButton_account.setText("显示账户")
        else:
            self.original_width = self.width()  # 更新原始宽度
            self.setMinimumWidth(1800)
            self.setMaximumWidth(1800)
            self.pushButton_account.setText("隐藏账户")

        self.is_maximized = not self.is_maximized  # 切换状态

    def on_reminder_clicked(self):
        newWin = ReminderDialog(self)
        newWin.exec_()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.FocusIn:
            if obj in (self.doubleSpinBox_stop_loss_price, self.doubleSpinBox_cost_price, self.spinBox_position_quantity, self.doubleSpinBox_take_profit_price, self.lineEdit_dynamic_equity):
                self.previous_focus_widget = obj
                # self.pushButton_ocr.setEnabled(True)
                utils.set_num_lock(True)

        if event.type() == QtCore.QEvent.FocusOut:
            if self.selected_future != None:
                if obj in (
                        self.doubleSpinBox_stop_loss_price,
                        self.doubleSpinBox_cost_price,
                        self.doubleSpinBox_take_profit_price
                ):
                    min_step = obj.property("minStep")
                    current_value = obj.value()
                    # 计算最接近的合法值
                    validated_value = round(current_value / min_step) * min_step
                    obj.setValue(validated_value)

        #
        # elif event.type() == QtCore.QEvent.FocusOut:
        #     if obj in (self.doubleSpinBox_stop_loss_price, self.doubleSpinBox_cost_price):
        #         if not (self.doubleSpinBox_stop_loss_price.hasFocus() or self.doubleSpinBox_cost_price.hasFocus() or self.pushButton_ocr.hasFocus()):
        #             self.pushButton_ocr.setEnabled(False)
        return super().eventFilter(obj, event)

    def on_ocr_clicked(self):
        pass
        # print("OCR button clicked")
        # if self.previous_focus_widget:
        #     self.previous_focus_widget.setFocus()  # 将焦点返回到之前的控件
        # self.transparent_window = TransparentWindow(self.previous_focus_widget)
        # self.transparent_window.show()

    def show_context_menu(self, position):
        indexes = self.tableWidget.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            position_obj = self.positions[row]
            print(f"Right-clicked row: {row}, Object: {position_obj}")

            menu = QMenu()
            custom_delete_action_item = CustomMenuItem("    删    除    ", menu)
            custom_delete_action_item.clicked.connect(lambda: self.delete_row(position_obj))
            delete_action = QWidgetAction(menu)
            delete_action.setDefaultWidget(custom_delete_action_item)
            menu.addAction(delete_action)

            add_position_action_item = CustomMenuItem("    加    仓    ", menu)
            add_position_action_item.clicked.connect(lambda: self.add_position(position_obj))
            add_position_action = QWidgetAction(menu)
            add_position_action.setDefaultWidget(add_position_action_item)
            menu.addAction(add_position_action)

            menu.exec_(self.tableWidget.viewport().mapToGlobal(position))

    def delete_row(self, position_obj):
        self.db_helper.delete_futures_position(position_obj)
        self.update_account_and_position_info()

    def add_position(self, position_obj):
        add_position_win = AddPositionDialog(self, position_obj, self.db_helper)
        add_position_win.position_saved.connect(self.update_account_and_position_info)
        add_position_win.exec_()

    def update_account_and_position_info(self):
        self.update_account_info()
        self.load_all_futures_position_to_table()

    def on_table_row_clicked(self, row, column):
        if row < len(self.positions):
            position_obj = self.positions[row]
            self.set_position_info(position_obj)

    def set_position_info(self, position_obj):
        self.position_bean = position_obj

        product_index = self.products_list.index(self.position_bean.product_name)

        # 设置futures_type_view的当前索引
        self.comboBox_futures_type.setCurrentIndex(product_index)

        # 设置其他视图控件的值
        self.doubleSpinBox_stop_loss_price.setValue(self.position_bean.stop_loss_price)
        self.doubleSpinBox_cost_price.setValue(self.position_bean.cost_price)
        self.spinBox_position_quantity.setValue(self.position_bean.position_quantity)

        # 设置操作方向的单选按钮
        self.radioButton_long.setChecked(self.position_bean.operation_direction == 1)
        self.radioButton_short.setChecked(self.position_bean.operation_direction == -1)

        self.comboBox_futures_type.setEnabled(False)
        self.radioButton_long.setEnabled(False)
        self.radioButton_short.setEnabled(False)

    def on_short_term_trading(self):
        self.showMinimized()

        self.short_term_trading_window = ShortTermTradingDialog()  # 保存为成员变量
        self.short_term_trading_window.show()

    def on_ths_helper_clicked(self):
        if self.helper_dialog.isVisible():
            self.helper_dialog.hide()  # 如果可见则隐藏
        else:
            self.helper_dialog.show()  # 否则显示对话框

    def calculate(self):
        if self.selected_future is None or not self.doubleSpinBox_stop_loss_price.lineEdit().text() or not self.doubleSpinBox_cost_price.lineEdit().text() or not self.spinBox_position_quantity.lineEdit().text():
            return

        try:
            stop_loss_price = self.doubleSpinBox_stop_loss_price.value()
            cost_price = self.doubleSpinBox_cost_price.value()
            position_quantity = self.spinBox_position_quantity.value()

            trading_units = self.selected_future.trading_units
            margin_ratio = self.selected_future.margin_ratio

            position_factor = 1 if self.radioButton_long.isChecked() else -1



            # Calculate current values
            stop_loss_amount = (stop_loss_price - cost_price) * position_quantity * trading_units * position_factor
            stop_loss_text = "1.止盈金额" if position_factor * (cost_price - stop_loss_price) < 0 else "1.止损金额"
            stop_loss_color = "red" if stop_loss_text == "1.止盈金额" else "black"

            take_profit_price_amount = 0
            profit_loss_ratio = 0

            if self.doubleSpinBox_take_profit_price.value() != self.doubleSpinBox_take_profit_price.minimum():
                take_profit_price = self.doubleSpinBox_take_profit_price.value()
                take_profit_price_amount = (take_profit_price - cost_price) * position_quantity * trading_units * position_factor

                # Calculate profit-loss ratio based on position_bean
                if self.position_bean is None:
                    # Use stop_loss_amount for calculation
                    if abs(stop_loss_amount) > 0:
                        profit_loss_ratio = abs(take_profit_price_amount / stop_loss_amount)
                else:
                    # Use self.position_bean.initial_stop_loss for calculation
                    initial_stop_loss = self.position_bean.initial_stop_loss
                    if abs(initial_stop_loss) > 0:
                        profit_loss_ratio = abs(take_profit_price_amount / initial_stop_loss)

            position_value = cost_price * position_quantity * trading_units
            margin_amount = position_value * margin_ratio / 100

            if self.position_bean is None:
                # New object, maintain current logic

                if self.doubleSpinBox_take_profit_price.value() == self.doubleSpinBox_take_profit_price.minimum():
                    result = (
                        f'<span style="color:{stop_loss_color};">{stop_loss_text}: {stop_loss_amount:.0f}</span><br>'
                        f'2.头寸价值: {position_value:.0f}<br>'
                        f'3.保证金金额: {margin_amount:.0f}<br>'
                    )
                else:
                    result = (
                        f'<span style="color:{stop_loss_color};">{stop_loss_text}: {stop_loss_amount:.0f}</span><br>'
                        f'2.头寸价值: {position_value}<br>'
                        f'3.保证金金额: {margin_amount:.0f}<br>'
                        f'4.止盈金额: {take_profit_price_amount:.0f}，盈亏比: {profit_loss_ratio:.2f}<br>'
                    )
            else:
                # Existing object, show changes with arrows
                previous_stop_loss_amount = self.position_bean.profit_loss_amount
                previous_position_value = self.position_bean.product_value
                previous_margin_amount = previous_position_value * margin_ratio / 100

                previous_stop_loss_text = "1.止盈金额" if previous_stop_loss_amount > 0 else "1.止损金额"
                previous_stop_loss_color = "red" if previous_stop_loss_text == "1.止盈金额" else "black"

                if self.doubleSpinBox_take_profit_price.value() == self.doubleSpinBox_take_profit_price.minimum():
                    result = (
                        f'<span style="color:{previous_stop_loss_color};">{previous_stop_loss_text}: {previous_stop_loss_amount:.0f} -> '
                        f'<span style="color:{stop_loss_color};">{stop_loss_amount:.0f}</span></span><br>'
                        f'2.头寸价值: {previous_position_value:.0f} -> {position_value:.0f}<br>'
                        f'3.保证金金额: {previous_margin_amount:.0f} -> {margin_amount:.0f}<br>'
                    )
                else:
                    result = (
                        f'<span style="color:{previous_stop_loss_color};">{previous_stop_loss_text}: {(previous_stop_loss_amount):.0f} -> '
                        f'<span style="color:{stop_loss_color};">{(stop_loss_amount):.0f}</span></span><br>'
                        f'2.头寸价值: {previous_position_value:.0f} -> {position_value:.0f}<br>'
                        f'3.保证金金额: {previous_margin_amount:.0f} -> {margin_amount:.0f}<br>'
                        f'4.止盈金额: {take_profit_price_amount:.0f}，盈亏比: {profit_loss_ratio:.2f}<br>'
                    )

            self.textBrowser.setHtml(result)

        except ValueError:
            self.textBrowser.setText("Invalid input")


class CustomMenuItem(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(text, self)
        self.label.setFont(QFont("宋体", 11))
        self.label.setAlignment(Qt.AlignCenter)

        # 设置样式表
        self.label.setStyleSheet("""
            QLabel {
                padding: 10px 20px 10px 20px;  # 上下左右的边距
                background-color: white;  # 默认背景颜色
            }
            QLabel:hover {
                background-color: lightgray;  # 鼠标悬停时的背景颜色
            }
        """)

        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # 发送点击信号
            self.parent().close()  # 关闭菜单


class RadioButtonEventFilter(QtCore.QObject):
    def __init__(self, radioButton_long, radioButton_short):
        super().__init__()
        self.radioButton_long = radioButton_long
        self.radioButton_short = radioButton_short

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                if obj == self.radioButton_long:
                    self.radioButton_short.setChecked(True)
                    self.radioButton_short.setFocus()
                    return True
                elif obj == self.radioButton_short:
                    self.radioButton_long.setChecked(True)
                    self.radioButton_long.setFocus()
                    return True
        return super().eventFilter(obj, event)
