from multiprocessing import Process

from PyQt5.QtWidgets import (QMainWindow, QWidget, QLineEdit, QLabel, QFrame, QGridLayout,
                             QMessageBox, QTableWidget, QHeaderView, QComboBox, QPushButton,
                             QTableWidgetItem)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QFont

from utils import get_integer, get_float
from connection import process_socket

from DatabaseConnection import DatabaseGUI


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.database = DatabaseGUI()

        self.setGeometry(300, 300, 1200, 800)
        self.setWindowTitle("System")
        self.setWindowIcon(QIcon("iconSystem.jpg"))

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.showDatabaseWidget = ShowDatabaseWidget(self)
        self.showDatabaseWidget.setFixedSize(1420, 500)
        self.layout.addWidget(self.showDatabaseWidget, *(1, 0, 1, 6))

        self.connectionTable = ConnectionTable(self)
        self.connectionTable.setFixedSize(580, 300)
        self.layout.addWidget(self.connectionTable, *(2, 0, 1, 1))

        self.add_record_widget = AddRecordWidget(self)
        self.add_record_widget.setFixedSize(300, 300)
        self.layout.addWidget(self.add_record_widget, *(2, 2, 1, 1))

        self.show_history_widget = ShowHistoryWidget(self)
        self.show_history_widget.setFixedSize(500, 300)
        self.layout.addWidget(self.show_history_widget, *(2, 1, 1, 1))

        self.show()
        return


class ConnectionTable(QWidget):
    COLUMN_NUMBER = 4

    def __init__(self, main_window):
        QWidget.__init__(self)
        self.main_window = main_window
        self.layout = QGridLayout(self)
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.main_window.database.get_connections_row_number())

        self.tableWidget.setColumnCount(ConnectionTable.COLUMN_NUMBER)
        self.tableWidget.setHorizontalHeaderLabels(["IP", "Port", "User", "Time"])

        self.header = self.tableWidget.horizontalHeader()
        self.header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.refresh_table()

        self.tableWidget.move(0, 0)
        self.layout.addWidget(self.tableWidget, *(0, 0, 1, 1))

        for i in range(5):
            p = Process(target=process_socket, args=(7005+i,))
            p.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_table)
        self.timer.start(1000)

        return

    def refresh_table(self):
        self.tableWidget.setRowCount(self.main_window.database.get_connections_row_number())

        for row_number, row in enumerate(self.main_window.database.get_active_connections_table()):
            for column_number, cell in enumerate(row):
                if column_number == 0:
                    continue
                self.tableWidget.setItem(row_number, column_number-1, QTableWidgetItem(str(cell)))

        self.layout.addWidget(self.tableWidget, *(0, 0, 1, 1))
        return


class AddRecordWidget(QWidget):
    def __init__(self, main_window):
        QWidget.__init__(self)

        self.layout = QGridLayout(self)
        self.main_window = main_window

        labels = {(1, 0): "Name:", (2, 0): "Surname:",
                  (3, 0): "Phone:", (4, 0): "Login:", (5, 0): "Password:",
                  (6, 0): "Balance:", (7, 0): "Status:"}

        for pos, name in labels.items():
            x, y = pos
            label = QLabel()
            label.setText(name)
            label.setAlignment(Qt.AlignRight)
            label.setFont(QFont('Arial', 10))
            self.layout.addWidget(label, x, y)

        self.textboxName = QLineEdit(self)
        self.textboxName.setFixedSize(150, 25)
        self.layout.addWidget(self.textboxName, *(1, 1, 1, 1))

        self.textboxSurname = QLineEdit(self)
        self.textboxSurname.setFixedSize(150, 25)
        self.layout.addWidget(self.textboxSurname, *(2, 1, 1, 1))

        self.textboxPhone = QLineEdit(self)
        self.textboxPhone.setFixedSize(150, 25)
        self.layout.addWidget(self.textboxPhone, *(3, 1, 1, 1))

        self.textboxLogin = QLineEdit(self)
        self.textboxLogin.setFixedSize(150, 25)
        self.layout.addWidget(self.textboxLogin, *(4, 1, 1, 1))

        self.textboxPassword = QLineEdit(self)
        self.textboxPassword.setFixedSize(150, 25)
        self.layout.addWidget(self.textboxPassword, *(5, 1, 1, 1))

        self.textboxBalance = QLineEdit(self)
        self.textboxBalance.setFixedSize(150, 25)
        self.layout.addWidget(self.textboxBalance, *(6, 1, 1, 1))

        self.selectStatus = QComboBox(self)
        self.selectStatus.setFixedSize(150, 25)
        self.selectStatus.addItem("Active")
        self.selectStatus.addItem("Blocked")
        self.layout.addWidget(self.selectStatus, *(7, 1, 1, 1))

        self.newRecordButton = QPushButton(self, text="Add")
        self.newRecordButton.setFixedSize(150, 40)
        self.newRecordButton.clicked.connect(self.add_new_record)
        self.layout.addWidget(self.newRecordButton, *(8, 1, 1, 1))

        self.setLayout(self.layout)
        return

    def add_new_record(self):

        name = self.textboxName.text()
        surname = self.textboxSurname.text()
        phone = get_integer(self.textboxPhone.text())
        login = self.textboxLogin.text()
        password = self.textboxPassword.text()
        balance = get_float(self.textboxBalance.text())
        status = self.selectStatus.currentText() == "Active"

        # data validation
        if not (name and surname and phone and login and password and balance is not None):
            QMessageBox.about(self.main_window, "Error", "Fields cannot be empty.")
            return
        if not (name.isalpha() and surname.isalpha() and len(str(phone)) == 9):
            QMessageBox.about(self.main_window, "Error", "Invalid data.")
            return
        if self.main_window.database.is_in_database("login", login):
            QMessageBox.about(self.main_window, "Error", "Login already used.")
            return

        self.main_window.database.insert_row_in_database(name, surname, phone, login, password, balance, status)
        self.main_window.showDatabaseWidget.refresh()

        return


class ShowDatabaseWidget(QWidget):
    COLUMN_NAMES = {0: "name", 1: "surname", 2: "phone", 3: "login", 4: "password",
                    5: "balance", 6: "attempts", 7: "activity", 8: "status"}

    def __init__(self, main_window):
        QWidget.__init__(self)

        self.main_window = main_window
        self.sorting_parameter = "name"
        self.sorting_status = False     # it allows to sort in the ascending and descending order
        self.database_table = None

        self.layout = QGridLayout(self)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.main_window.database.get_clientdata_row_number())
        self.tableWidget.setColumnCount(11)

        self.tableWidget.setHorizontalHeaderLabels(list(ShowDatabaseWidget.COLUMN_NAMES.values()) + ["", ""])

        self.header = self.tableWidget.horizontalHeader()
        self.header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.refresh()  # it fills table content

        self.tableWidget.move(0, 0)
        self.layout.addWidget(self.tableWidget, *(0, 0, 1, 1))
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.database_header_clicked)

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.refresh())
        self.timer.start(1000)

        return

    def show_history(self):
        user_id = self.sender().objectName()
        history = self.main_window.database.get_history(user_id)
        history_table = [row.split(' ') for row in history.split('\n')][:-1]
        # history ends with the new line sign, so one needs to exclude the last element
        self.main_window.show_history_widget.refresh(history_table)
        return

    def change_status(self):
        record_id = self.sender().objectName()     # sending button name is the id of a record
        self.main_window.database.change_clientdata_status(record_id)
        self.refresh()

    def delete_record(self):
        record_id = self.sender().objectName()
        self.main_window.database.delete_clientdata_row(record_id)
        self.refresh()

    def database_header_clicked(self, header_number):
        if header_number > 7:   # only columns with data can be sorted
            return
        self.sorting_parameter = ShowDatabaseWidget.COLUMN_NAMES[header_number]
        self.sorting_status = not self.sorting_status
        self.refresh()
        return

    def refresh(self):
        self.tableWidget.setRowCount(self.main_window.database.get_clientdata_row_number())
        self.database_table = self.main_window.database.get_clientdata_df(self.sorting_parameter, self.sorting_status)
        self.write_table_content()
        self.layout.addWidget(self.tableWidget, *(0, 0, 1, 1))
        return

    def write_table_content(self):
        for row_number, row in enumerate(self.database_table.values.tolist()):
            for column_number, cell in enumerate(row):
                if column_number == 0:      # it creates buttons in a row

                    statusBtn = QPushButton(self.tableWidget)
                    statusBtn.setText(str(row[9]))
                    statusBtn.setObjectName(str(row[0]))
                    statusBtn.clicked.connect(self.change_status)
                    self.tableWidget.setCellWidget(row_number, 8, statusBtn)

                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText('Delete')
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(row_number, 9, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('History')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(row_number, 10, historyBtn)

                if column_number in range(1, 8+1):      # it writes content of the table
                    self.tableWidget.setItem(row_number, column_number - 1, QTableWidgetItem(str(cell)))
        return


class ShowHistoryWidget(QWidget):
    def __init__(self, main_window):
        QWidget.__init__(self)

        self.main_window = main_window
        self.lay = QGridLayout(self)

        self.main_window.database.cursor.execute('SELECT * FROM ClientData')

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setHorizontalHeaderLabels(["Type", "Amount", "Time"])

        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))

    def refresh(self, data):
        self.tableWidget.setRowCount(len(data))

        for row_number, row in enumerate(data):
            for column_number, cell in enumerate(row):
                if column_number < 2:
                    self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(cell)))
                if column_number == 2:
                    day, time = cell, row[3]
                    self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(f"{day} {time}"))

        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))
