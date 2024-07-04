from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from database.db_helper import DBHelper
from ui.reminder_ui import Ui_Dialog


class ReminderDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.setWindowTitle("Zengguo.Liang")

        self.setWindowFlags(
            self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint)

        self.db_helper = DBHelper()
        self.initDB()

        self.initUI()

    def initDB(self):
        if self.db_helper.is_reminder_table_empty():
            self.db_helper.insert_reminder('09:30', False)
            self.db_helper.insert_reminder('10:00', False)
            self.db_helper.insert_reminder('10:45', False)
            self.db_helper.insert_reminder('11:15', False)
            self.db_helper.insert_reminder('13:45', False)
            self.db_helper.insert_reminder('14:15', False)
            self.db_helper.insert_reminder('14:45', False)
            self.db_helper.insert_reminder('15:00', False)
            self.db_helper.insert_reminder('21:30', False)
            self.db_helper.insert_reminder('22:00', False)
            self.db_helper.insert_reminder('22:30', False)
            self.db_helper.insert_reminder('23:00', False)

    def initUI(self):
        self.in_set_all_time_status = False
        self.in_set_each_time_status = False

        self.checkBox_0930.setChecked(self.db_helper.get_reminder_bean('09:30').is_checked)
        self.checkBox_1000.setChecked(self.db_helper.get_reminder_bean('10:00').is_checked)
        self.checkBox_1045.setChecked(self.db_helper.get_reminder_bean('10:45').is_checked)
        self.checkBox_1115.setChecked(self.db_helper.get_reminder_bean('11:15').is_checked)
        self.checkBox_1345.setChecked(self.db_helper.get_reminder_bean('13:45').is_checked)
        self.checkBox_1415.setChecked(self.db_helper.get_reminder_bean('14:15').is_checked)
        self.checkBox_1445.setChecked(self.db_helper.get_reminder_bean('14:45').is_checked)
        self.checkBox_1500.setChecked(self.db_helper.get_reminder_bean('15:00').is_checked)
        self.checkBox_2130.setChecked(self.db_helper.get_reminder_bean('21:30').is_checked)
        self.checkBox_2200.setChecked(self.db_helper.get_reminder_bean('22:00').is_checked)
        self.checkBox_2230.setChecked(self.db_helper.get_reminder_bean('22:30').is_checked)
        self.checkBox_2300.setChecked(self.db_helper.get_reminder_bean('23:00').is_checked)

        if (self.checkBox_0930.isChecked() and
                self.checkBox_1000.isChecked() and
                self.checkBox_1045.isChecked() and
                self.checkBox_1115.isChecked() and
                self.checkBox_1345.isChecked() and
                self.checkBox_1415.isChecked() and
                self.checkBox_1445.isChecked() and
                self.checkBox_1500.isChecked() and
                self.checkBox_2130.isChecked() and
                self.checkBox_2200.isChecked() and
                self.checkBox_2230.isChecked() and
                self.checkBox_2300.isChecked()
        ):
            self.checkBox_all_time.setChecked(True)
        else:
            self.checkBox_all_time.setChecked(False)

        self.setup_connections()

    def setup_connections(self):
        self.checkBox_all_time.stateChanged.connect(lambda: self.checkBox_state_change_all_time())
        self.checkBox_0930.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1000.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1045.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1115.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1345.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1415.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1445.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_1500.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_2130.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_2200.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_2230.stateChanged.connect(lambda: self.checkBox_state_change())
        self.checkBox_2300.stateChanged.connect(lambda: self.checkBox_state_change())

        self.pushButton_save_reminder.clicked.connect(lambda: self.save_reminder())

    def save_reminder(self):
        self.db_helper.update_reminder_bean(reminder_time='09:30', is_checked=self.checkBox_0930.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='10:00', is_checked=self.checkBox_1000.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='10:45', is_checked=self.checkBox_1045.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='11:15', is_checked=self.checkBox_1115.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='13:45', is_checked=self.checkBox_1345.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='14:15', is_checked=self.checkBox_1415.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='14:45', is_checked=self.checkBox_1445.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='15:00', is_checked=self.checkBox_1500.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='21:30', is_checked=self.checkBox_2130.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='22:00', is_checked=self.checkBox_2200.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='22:30', is_checked=self.checkBox_2230.isChecked())
        self.db_helper.update_reminder_bean(reminder_time='23:00', is_checked=self.checkBox_2300.isChecked())

        self.close()

    def checkBox_state_change_all_time(self):

        if self.in_set_each_time_status:
            return

        self.in_set_all_time_status = True

        self.checkBox_0930.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1000.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1045.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1115.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1345.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1415.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1445.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_1500.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_2130.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_2200.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_2230.setChecked(self.checkBox_all_time.isChecked())
        self.checkBox_2300.setChecked(self.checkBox_all_time.isChecked())

        self.in_set_all_time_status = False

    def checkBox_state_change(self):

        if self.in_set_all_time_status:
            return

        self.in_set_each_time_status = True

        if (self.checkBox_0930.isChecked() and
                self.checkBox_1000.isChecked() and
                self.checkBox_1045.isChecked() and
                self.checkBox_1115.isChecked() and
                self.checkBox_1345.isChecked() and
                self.checkBox_1415.isChecked() and
                self.checkBox_1445.isChecked() and
                self.checkBox_1500.isChecked() and
                self.checkBox_2130.isChecked() and
                self.checkBox_2200.isChecked() and
                self.checkBox_2230.isChecked() and
                self.checkBox_2300.isChecked()
        ):
            self.checkBox_all_time.setChecked(True)
        else:
            self.checkBox_all_time.setChecked(False)

        self.in_set_each_time_status = False

