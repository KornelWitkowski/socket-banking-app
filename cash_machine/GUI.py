import socket
from utils import get_float

from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QWidget, QPushButton, QMainWindow, QTableWidgetItem, QTableWidget, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QIcon

from Communicates import Communicates
from CashMachineConnectionService import CashMachineConnectionService


TCP_IP = '127.0.0.1'
TCP_PORT = 7008


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.login_window = None
        self.logged_in_window = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((TCP_IP, TCP_PORT))
        self.connection_service = CashMachineConnectionService(self.socket)

        self.setGeometry(300, 300, 500, 450)
        self.setWindowTitle("Cash machine")
        self.setWindowIcon(QIcon("iconMain.jpg"))

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.create_login_window()

        self.show()
        return

    def create_login_window(self):
        self.login_window = LoginWidget(self)
        self.login_window.setFixedSize(500, 250)
        self.layout.addWidget(self.login_window, *(1, 1, 1, 1))
        return

    def create_logged_in_window(self):
        self.logged_in_window = LoggedInWindow(self)
        self.logged_in_window.setFixedSize(320, 400)
        self.layout.addWidget(self.logged_in_window)
        return

    def send_communicate(self, communicate):
        return self.connection_service.send_communicate(communicate)

    def send_dict_and_receive_response(self, dictionary):
        return self.connection_service.send_dict_and_receive_response(dictionary)

    def send_communicate_and_receive_response(self, communicate):
        return self.connection_service.send_communicate_and_receive_response(communicate)

    def send_communicate_and_receive_string(self, communicate):
        return self.connection_service.send_communicate_and_receive_string(communicate)


class LoginWidget(QWidget):
    def __init__(self, main_window):
        QWidget.__init__(self)
        self.main_window = main_window
        self.layout = QGridLayout(self)

        self.labelLogin = QLabel("Login:")
        self.labelLogin.setFont(QFont('Arial', 14))
        self.labelLogin.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelLogin, *(1, 0, 1, 1))
        self.textboxLogin = QLineEdit(self)
        self.textboxLogin.setFont(QFont('Arial', 14))
        self.textboxLogin.setFixedSize(200, 50)
        self.layout.addWidget(self.textboxLogin, *(2, 0, 1, 1))

        self.labelPassword = QLabel("Password:")
        self.labelPassword.setFont(QFont('Arial', 14))
        self.labelPassword.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelPassword, *(3, 0, 1, 1))
        self.textboxPassword = QLineEdit(self)
        self.textboxPassword.setEchoMode(QLineEdit.Password)
        self.textboxPassword.setFont(QFont('Arial', 14))
        self.textboxPassword.setFixedSize(200, 50)
        self.layout.addWidget(self.textboxPassword, *(4, 0, 1, 1))

        self.setBtn = QPushButton(text='Log in')
        self.setBtn.setFont(QFont('Arial', 14))
        self.setBtn.setFixedSize(200, 45)
        self.setBtn.clicked.connect(self.push_login_button)
        self.layout.addWidget(self.setBtn, *(5, 0))

        return

    def create_logged_in_window(self):
        self.setParent(None)        # turn off the current login window
        self.main_window.create_logged_in_window()
        return

    def push_login_button(self):
        login, password = self.textboxLogin.text(), self.textboxPassword.text()
        login_dict = {"Login": login, "Password": password}

        response = self.main_window.send_dict_and_receive_response(login_dict)

        if response == Communicates.LOGGED_IN.value:
            self.create_logged_in_window()
            return
        QMessageBox.about(self, "Information", f"System communicate: {str(Communicates(response))}")


class LoggedInWindow(QWidget):
    def __init__(self, main_window):
        QWidget.__init__(self)
        self.main_window = main_window

        Data = self.main_window.send_communicate_and_receive_response(Communicates.GIVE_ACCOUNT_DATA)

        self.layout = QGridLayout(self)
        self.labelTime = QLabel(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss'))
        self.labelTime.setFont(QFont('Arial', 12))
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_time)
        self.layout.addWidget(self.labelTime, 0, 0, 1, 2)
        self.timer.start(1000)

        self.labelName = QLabel(Data["name"] + " " + Data["surname"])
        self.labelName.setFont(QFont('Arial', 12))
        self.layout.addWidget(self.labelName, 1, 0, 1, 2)

        self.labelBalance = QLabel("Balance:  " + str(Data["balance"]))
        self.labelBalance.setFont(QFont('Arial', 12))
        self.layout.addWidget(self.labelBalance, 2, 0, 1, 2)

        self.textboxAmount = QLineEdit(self)
        self.textboxAmount.setFixedSize(303, 40)
        self.textboxAmount.setFont(QFont('Arial', 12))
        self.layout.addWidget(self.textboxAmount, *(3, 0, 1, 1))

        btns = {(4, 0): "Deposit", (4, 1): "Payout",
                (5, 0): "History", (5, 1): "Data",
                (6, 0): "Change password", (6, 1): "Block account"}

        for pos, name in btns.items():
            x, y = pos
            btn = QPushButton()
            btn.setText(name)
            btn.clicked.connect(self.push_button)
            btn.setFixedSize(150, 45)
            btn.setObjectName(name)
            self.layout.addWidget(btn, x, y)

        self.setBtn = QPushButton(text='Log out')
        self.setBtn.setFixedSize(303, 45)
        self.setBtn.clicked.connect(self.log_out)
        self.layout.addWidget(self.setBtn, *(8, 0, 1, 1))

    def push_button(self):
        action_name = self.sender().objectName()

        if action_name in ("Deposit", "Payout"):
            self.make_payment(action_name)
            return
        if action_name == "Change password":
            self.show_change_password_window()
            return
        if action_name == "Block account":
            self.service_block_account()
            return
        if action_name == "Data":
            self.show_data()
            return
        if action_name == "History":
            self.show_history()
            return
        return

    def show_time(self):
        self.labelTime.setText(self.get_time())

    def log_out(self, message="Logged out"):
        self.main_window.send_communicate(Communicates.LOGOUT)
        self.setParent(None)
        self.main_window.logout = LogoutWidget(self.main_window, message)
        self.main_window.logout.setFixedSize(500, 250)
        self.main_window.layout.addWidget(self.main_window.logout, *(1, 1, 1, 1))

    def get_amount(self):
        return get_float(self.textboxAmount.text())

    def get_time(self):
        return QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')

    def make_payment(self, action_name):
        amount = self.get_amount()
        if amount is None:
            return

        response = self.main_window.send_communicate_and_receive_response(Communicates.PAYMENT)
        if not response == Communicates.SEND_DICT.value:
            return

        payment_dict = {"transaction type": action_name, "amount": amount, "transaction time": self.get_time()}
        response = self.main_window.send_dict_and_receive_response(payment_dict)

        self.labelBalance.setText("Balance:  " + str(response["balance"]))
        return

    def show_data(self):
        data = self.main_window.send_communicate_and_receive_response(Communicates.GIVE_ACCOUNT_DATA)
        DataWindow(data, self).show()
        return

    def show_history(self):
        history = self.main_window.send_communicate_and_receive_string(Communicates.GIVE_HISTORY)
        HistoryWindow(history, self).show()
        return

    def show_change_password_window(self):
        ChangePasswordWindow(self.main_window)
        return

    def service_block_account(self):
        reply = QMessageBox.question(self, 'Block account', 'Are you sure you want to do it?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            response = self.main_window.send_communicate_and_receive_response(Communicates.BLOCK_ACCOUNT)
            if response == Communicates.ACCOUNT_HAS_BEEN_BLOCKED.value:
                self.log_out(message="Account has been blocked")
        return


class LogoutWidget(QWidget):
    def __init__(self, main_window, message):
        QWidget.__init__(self)
        self.layout = QGridLayout(self)
        self.main_window = main_window

        self.labelName = QLabel(message)
        self.labelName.setFont(QFont('Arial', 14))
        self.labelName.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelName, *(1, 0))

        self.closeBtn = QPushButton(text='Close')
        self.closeBtn.setFont(QFont('Arial', 14))
        self.closeBtn.setFixedSize(200, 45)
        self.closeBtn.clicked.connect(self.close)
        self.layout.addWidget(self.closeBtn, *(8, 0))

        return

    def close(self):
        self.setParent(None)
        self.main_window.login_window.textboxLogin.clear()
        self.main_window.login_window.textboxPassword.clear()
        self.main_window.layout.addWidget(self.main_window.login_window, *(1, 1, 1, 1))
        return


class ChangePasswordWindow(QMainWindow):
    def __init__(self, main_window):
        super(ChangePasswordWindow, self).__init__(parent=main_window)

        self.main_window = main_window
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle("Change password")
        self.setWindowIcon(QIcon("iconChangePassword.jpg"))

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)
        self.loginWin = ChangePasswordWidget(self, self.main_window)
        self.loginWin.setFixedSize(250, 250)
        self.layout.addWidget(self.loginWin, *(1, 1, 1, 1))

        self.show()

        return


class ChangePasswordWidget(QWidget):
    def __init__(self, parent, main_window):
        QWidget.__init__(self, parent=parent)
        self.main_window = main_window
        self.layout = QGridLayout(self)

        self.labelCurrentPassword = QLabel("Current password:")
        self.labelCurrentPassword.setFont(QFont('Arial', 12))
        self.labelCurrentPassword.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelCurrentPassword, *(3, 0, 1, 4))
        self.textboxCurrentPassword = QLineEdit(self)
        self.textboxCurrentPassword.setEchoMode(QLineEdit.Password)
        self.textboxCurrentPassword.setFont(QFont('Arial', 14))
        self.textboxCurrentPassword.setFixedSize(180, 30)
        self.layout.addWidget(self.textboxCurrentPassword, *(4, 0, 1, 4))

        self.labelNewPassword = QLabel("New password:")
        self.labelNewPassword.setFont(QFont('Arial', 12))
        self.labelNewPassword.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelNewPassword, *(6, 0, 1, 4))
        self.textboxNewPassword = QLineEdit(self)
        self.textboxNewPassword.setEchoMode(QLineEdit.Password)
        self.textboxNewPassword.setFont(QFont('Arial', 14))
        self.textboxNewPassword.setFixedSize(180, 30)
        self.layout.addWidget(self.textboxNewPassword, *(7, 0, 1, 4))

        self.labelConfirmedPassword = QLabel("Confirm password:")
        self.labelConfirmedPassword.setFont(QFont('Arial', 12))
        self.labelConfirmedPassword.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelConfirmedPassword, *(8, 0, 1, 4))
        self.textboxConfirmedPassword = QLineEdit(self)
        self.textboxConfirmedPassword.setEchoMode(QLineEdit.Password)
        self.textboxConfirmedPassword.setFont(QFont('Arial', 14))
        self.textboxConfirmedPassword.setFixedSize(180, 30)
        self.layout.addWidget(self.textboxConfirmedPassword, *(9, 0, 1, 4))

        self.setBtn = QPushButton(text='Decline')
        self.setBtn.setFont(QFont('Arial', 12))
        self.setBtn.setFixedSize(85, 30)
        self.setBtn.clicked.connect(self.decline)
        self.layout.addWidget(self.setBtn, *(10, 0, 1, 1))

        self.setBtn = QPushButton(text='Change')
        self.setBtn.setFont(QFont('Arial', 12))
        self.setBtn.setFixedSize(85, 30)
        self.setBtn.clicked.connect(self.confirm)
        self.layout.addWidget(self.setBtn, *(10, 1, 1, 1))

    def decline(self):
        Parent = self.parent().parent()
        Parent.close()

    def confirm(self):
        current_password = self.textboxCurrentPassword.text()
        new_password = self.textboxNewPassword.text()
        confirmed_password = self.textboxConfirmedPassword.text()
        response = self.main_window.send_communicate_and_receive_response(Communicates.CHANGE_PASSWORD)

        if not response == Communicates.SEND_DICT.value:
            return

        data = {"CurrentPassword": current_password,
                "NewPassword": new_password,
                "ConfirmedPassword": confirmed_password}

        response = self.main_window.send_dict_and_receive_response(data)

        QMessageBox.about(self, "Information", f"System communicate: {str(Communicates(response))}")
        Parent = self.parent().parent()
        Parent.close()


class DataWindow(QMainWindow):
    def __init__(self, data, parent=None):
        super(DataWindow, self).__init__(parent)

        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle("Account data")

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        for count, key in enumerate(data):
            if key == "history":
                break
            self.label = QLabel(str(key) + ": " + str(data[key]))
            self.label.setFont(QFont('Arial', 10))
            self.label.setAlignment(Qt.AlignLeft)
            self.layout.addWidget(self.label, *(count, 0, 1, 1))

        return


class HistoryWindow(QMainWindow):
    def __init__(self, history, parent=None):
        super(HistoryWindow, self).__init__(parent)

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)
        self.setGeometry(400, 300, 500, 400)
        self.setWindowTitle("History")

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setHorizontalHeaderLabels(["Type", "Amount", "Time"])

        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        history_table = [row.split(' ') for row in history.split('\n')][:-1]

        self.tableWidget.setRowCount(len(history_table))

        for row_number, row in enumerate(history_table):
            for column_number, cell in enumerate(row):
                if column_number < 2:
                    self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(cell)))
                if column_number == 2:
                    day, time = cell, row[3]
                    self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(f"{day} {time}"))

        self.tableWidget.move(0, 0)
        self.layout.addWidget(self.tableWidget, *(0, 0, 1, 1))
