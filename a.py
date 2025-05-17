import sys

from PyQt5.QtCore import QSortFilterProxyModel, Qt, QModelIndex
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QComboBox, QCompleter, QLineEdit)


# 自定义代理模型实现多条件过滤
class MultiFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        pattern = self.filterRegExp().pattern().lower()
        if not pattern:
            return True

        source = self.sourceModel()
        index = source.index(source_row, self.filterKeyColumn(), source_parent)

        # 获取显示文本（产品名称）
        display_text = source.data(index, Qt.DisplayRole).lower()
        # 获取拼音数据（存储在UserRole）
        pinyin = source.data(index, Qt.UserRole).lower()

        return pattern in display_text or pattern in pinyin


class ComboBox(QComboBox):
    def __init__(self, parent=None):
        super(ComboBox, self).__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.lineEdit().setPlaceholderText("输入拼音或产品名称搜索...")

        # 使用自定义代理模型
        self.proxy_model = MultiFilterProxyModel(self)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setSourceModel(self.model())

        # 配置自动完成
        self.completer = QCompleter(self.proxy_model, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)

        # 连接信号
        self.lineEdit().textEdited.connect(self.updateFilter)
        self.completer.activated.connect(self.on_completer_activated)

    def updateFilter(self, text):
        self.proxy_model.setFilterFixedString(text)

    def on_completer_activated(self, text):
        if index := self.findText(text) != -1:
            self.setCurrentIndex(index)
            self.activated[str].emit(self.currentText())

    def setModel(self, model):
        super().setModel(model)
        self.proxy_model.setSourceModel(model)
        self.completer.setModel(self.proxy_model)

    def setModelColumn(self, column):
        self.proxy_model.setFilterKeyColumn(column)
        super().setModelColumn(column)


class QComboBoxDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.data = [
            {'pinYin': 'YM', 'tradingCode': 'LG', 'tradingProduct': '原木', 'tradingUnits': '90', 'minimumPriceChange': '0.5', 'marginRatio': '8'},
            {'pinYin': 'JD', 'tradingCode': 'JD', 'tradingProduct': '鸡蛋', 'tradingUnits': '10', 'minimumPriceChange': '1', 'marginRatio': '8'},
            {'pinYin': 'HS', 'tradingCode': 'PK', 'tradingProduct': '花生', 'tradingUnits': '5', 'minimumPriceChange': '2', 'marginRatio': '8'},
            {'pinYin': 'PG', 'tradingCode': 'AP', 'tradingProduct': '苹果', 'tradingUnits': '10', 'minimumPriceChange': '1', 'marginRatio': '10'},
            {'pinYin': 'HZ', 'tradingCode': 'CJ', 'tradingProduct': '红枣', 'tradingUnits': '5', 'minimumPriceChange': '5', 'marginRatio': '12'},
            {'pinYin': 'SZ', 'tradingCode': 'LH', 'tradingProduct': '生猪', 'tradingUnits': '16', 'minimumPriceChange': '5', 'marginRatio': '12'},
            {'pinYin': 'NS', 'tradingCode': 'UR', 'tradingProduct': '尿素', 'tradingUnits': '20', 'minimumPriceChange': '1', 'marginRatio': '8'},
            {'pinYin': 'MG', 'tradingCode': 'SM', 'tradingProduct': '锰硅', 'tradingUnits': '5', 'minimumPriceChange': '2', 'marginRatio': '12'},
            {'pinYin': 'GT', 'tradingCode': 'SF', 'tradingProduct': '硅铁', 'tradingUnits': '5', 'minimumPriceChange': '2', 'marginRatio': '12'},
            {'pinYin': 'GYG', 'tradingCode': 'SI', 'tradingProduct': '工业硅', 'tradingUnits': '5', 'minimumPriceChange': '5', 'marginRatio': '9'},
            {'pinYin': 'DJG', 'tradingCode': 'PS', 'tradingProduct': '多晶硅', 'tradingUnits': '3', 'minimumPriceChange': '5', 'marginRatio': '9'},
            {'pinYin': 'TSL', 'tradingCode': 'LC', 'tradingProduct': '碳酸锂', 'tradingUnits': '1', 'minimumPriceChange': '20', 'marginRatio': '10'},
            {'pinYin': 'JYOX', 'tradingCode': 'EC', 'tradingProduct': '集运欧线', 'tradingUnits': '50', 'minimumPriceChange': '0.1', 'marginRatio': '12'},
        ]
        self.initUI()

    def initUI(self):
        self.setWindowTitle("商品搜索下拉框")
        self.resize(600, 400)
        layout = QVBoxLayout()

        self.label = QLabel('请选择商品')
        self.ComboBoxTest = ComboBox()

        # 添加数据到下拉框
        for item in self.data:
            self.ComboBoxTest.addItem(item['tradingProduct'])
            last_index = self.ComboBoxTest.count() - 1
            # 将拼音存储在UserRole
            self.ComboBoxTest.setItemData(last_index, item['pinYin'], Qt.UserRole)

        self.ComboBoxTest.currentIndexChanged.connect(self.selectionChange)

        layout.addWidget(self.label)
        layout.addWidget(self.ComboBoxTest)
        self.setLayout(layout)

    def selectionChange(self, i):
        self.label.setText(self.ComboBoxTest.currentText())
        self.label.adjustSize()
        print(f"当前选择: {self.ComboBoxTest.currentText()}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = QComboBoxDemo()
    w.show()
    sys.exit(app.exec_())
