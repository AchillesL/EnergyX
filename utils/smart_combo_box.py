# smart_combo_box.py
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from PyQt5.QtWidgets import QComboBox, QCompleter


class MultiFilterProxyModel(QSortFilterProxyModel):
    # 保持原有MultiFilterProxyModel实现不变
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        pattern = self.filterRegExp().pattern().lower()
        if not pattern:
            return True
        source = self.sourceModel()
        index = source.index(source_row, self.filterKeyColumn(), source_parent)

        display_text = source.data(index, Qt.DisplayRole).lower()
        pinyin = source.data(index, Qt.UserRole).lower()
        return pattern in display_text or pattern in pinyin


class SmartComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 保持原有SmartComboBox初始化逻辑不变
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("输入拼音/产品名搜索...")

        # 配置代理模型
        self.proxy_model = MultiFilterProxyModel(self)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setSourceModel(self.model())

        # 配置自动完成
        self.completer = QCompleter(self.proxy_model, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)

        # 信号连接
        self.lineEdit().textEdited.connect(self.proxy_model.setFilterFixedString)

    @classmethod
    def replace_existing_combobox(cls, old_combobox, parent_layout):
        """
        替换现有QComboBox为SmartComboBox的工厂方法
        :param old_combobox: 要被替换的原始QComboBox对象
        :param parent_layout: 包含原始控件的父布局
        :return: 新创建的SmartComboBox实例
        """
        # 保存原始属性
        original_name = old_combobox.objectName()
        style_sheet = old_combobox.styleSheet()
        font = old_combobox.font()
        palette = old_combobox.palette()

        # 在布局中找到原始控件的位置
        index = parent_layout.indexOf(old_combobox)
        if index == -1:
            raise ValueError("原始控件不在指定布局中")

        # 获取布局参数
        row, column, rowSpan, colSpan = parent_layout.getItemPosition(index)

        # 创建新控件
        new_combobox = cls(old_combobox.parentWidget())

        # 复制属性
        new_combobox.setObjectName(original_name)
        new_combobox.setStyleSheet(style_sheet)
        new_combobox.setFont(font)
        new_combobox.setPalette(palette)

        # 替换布局中的控件
        parent_layout.removeWidget(old_combobox)
        old_combobox.hide()
        parent_layout.addWidget(new_combobox, row, column, rowSpan, colSpan)

        return new_combobox

    def setModel(self, model):
        super().setModel(model)
        self.proxy_model.setSourceModel(model)
        self.completer.setModel(self.proxy_model)

    def setModelColumn(self, column):
        self.proxy_model.setFilterKeyColumn(column)
        super().setModelColumn(column)
