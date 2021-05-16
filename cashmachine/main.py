import sys
import socket
import time
import ast

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import json

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Cash machine")
        self.setWindowIcon(QIcon("iconMain.jpg"))

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.LoginWid = LoginWidget(self)
        self.LoginWid.setFixedSize(500, 250)
        self.layout.addWidget(self.LoginWid, *(1, 1, 1, 1))

        self.show()
        return


class LoginWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)
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
        self.setBtn.clicked.connect(self.loginbtn_push)
        self.layout.addWidget(self.setBtn, *(5, 0))

        return

    def loginbtn_push(self):

        Login = self.textboxLogin.text()
        Password = self.textboxPassword.text()
        data = {"Login": Login, "Password": Password}
        s.send(str.encode(str(data)))
        answer = s.recv(BUFFER_SIZE)

        Parent = self.parent().parent()

        if answer.decode() == "Ok":
            self.setParent(None)
            Parent.LoggedinWin = LoggedinWindow(self)
            Parent.LoggedinWin.setFixedSize(500, 250)
            Parent.layout.addWidget(Parent.LoggedinWin, *(1, 1, 1, 1))


class LoggedinWindow(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        time.sleep(0.5)
        s.send(str.encode("Give me all that you got now!"))
        answer = s.recv(BUFFER_SIZE)

        #DecodedData = ast.literal_eval(answer.decode()) Czemu to nie działa?
        json_acceptable_string = answer.decode().replace("'", "\"")
        Data = json.loads(json_acceptable_string)

        self.layout = QGridLayout(self)
        self.labelTime = QLabel(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss'))
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_time)
        self.layout.addWidget(self.labelTime, 0, 1, 1, 2)
        self.timer.start(1000)

        self.labelName = QLabel(Data["name"] + " " + Data["surname"])
        self.layout.addWidget(self.labelName, 1, 1, 1, 2)

        self.labelBalance = QLabel("Balance:  " + str(Data["balance"]))
        self.layout.addWidget(self.labelBalance, 2, 1, 1, 2)

        self.textboxAmount = QLineEdit(self)
        self.textboxAmount.setFixedSize(100, 25)
        self.layout.addWidget(self.textboxAmount, *(3, 1, 1, 1))

        btns = {(4, 0): "Deposit", (4, 1): "Payout",
                (5, 0): "History", (5, 1): "Data",
                (6, 0): "Change password", (6, 1): "Block account"}

        for pos, name in btns.items():
            x, y = pos
            btn = QPushButton()
            btn.setText(name)
            btn.clicked.connect(self.push_button)
            btn.setObjectName(name)
            self.layout.addWidget(btn, x, y)

        self.setBtn = QPushButton(text='Log out')
        self.setBtn.setFont(QFont('Arial', 14))
        self.setBtn.setFixedSize(200, 45)
        self.setBtn.clicked.connect(self.log_out)
        self.layout.addWidget(self.setBtn, *(8, 0))

    def push_button(self):
        sendingButtonName = self.sender().objectName()
        amount = self.textboxAmount.text()

        if sendingButtonName == "Deposit":

            time = QDateTime.currentDateTime()
            timeDisplay = time.toString('yyyy-MM-dd hh:mm:ss dddd')
            try:
                if int(amount) >= 0:
                    data = {"transaction type": "Deposit", "amount": amount, "transaction time": timeDisplay}
                    s.send(str.encode(str(data)))
                    answer = s.recv(BUFFER_SIZE)

                    DecodedData = ast.literal_eval(answer.decode())
                    self.labelBalance.setText("Balance:  " + str(DecodedData["balance"]))
            except:
                pass

        elif sendingButtonName == "Payout":

            time = QDateTime.currentDateTime()
            timeDisplay = time.toString('yyyy-MM-dd hh:mm:ss dddd')
            try:
                if int(amount) >= 0:
                    data = {"transaction type": "Payout", "amount": amount, "transaction time": timeDisplay}
                    s.send(str.encode(str(data)))
                    answer = s.recv(BUFFER_SIZE)

                    if answer.decode() == "Not enough money.":
                        QMessageBox.about(self, "Error", "Not enough money.")
                    else:
                        DecodedData = ast.literal_eval(answer.decode())
                        self.labelBalance.setText("Balance:  " + str(DecodedData["balance"]))
            except:
                pass
        elif sendingButtonName == "Change password":
            self.changePassword = ChangePasswordWindow()
            self.changePassword.show()
        elif sendingButtonName == "Block account":
            reply = QMessageBox.question(self, 'Block account', 'Are you sure you want to do it?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                s.send(str.encode(str("Block account")))
                answer = s.recv(BUFFER_SIZE)

                if answer.decode() == "Account has been blocked":
                    self.log_out(message="Account has been blocked")

        elif sendingButtonName == "Data":
            s.send(str.encode(str("Show data")))
            answer = s.recv(BUFFER_SIZE)
            DecodedData = ast.literal_eval(answer.decode())
            self.DataWin = DataWindow(DecodedData)
            self.DataWin.show()

    def show_time(self):
        time = QDateTime.currentDateTime()
        timeDisplay = time.toString('yyyy-MM-dd hh:mm:ss')
        self.labelTime.setText(timeDisplay)

    def log_out(self, **kwargs):
        message = kwargs.get('message', "Logged out")
        s.send(str.encode("Logout"))
        Parent = self.parent().parent()
        self.setParent(None)
        Parent.logout = LogoutWidget(self, message)
        Parent.logout.setFixedSize(500, 250)
        Parent.layout.addWidget(Parent.logout, *(1, 1, 1, 1))


class LogoutWidget(QWidget):
    def __init__(self, parent, message):
        QWidget.__init__(self, parent=parent)
        self.layout = QGridLayout(self)

        self.labelName = QLabel(message)
        self.labelName.setFont(QFont('Arial', 14))
        self.labelName.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.labelName, *(1, 0))

        self.bt1 = QPushButton(text='Zamknij')
        self.bt1.setFont(QFont('Arial', 14))
        self.bt1.setFixedSize(200, 45)
        self.bt1.clicked.connect(self.close)
        self.layout.addWidget(self.bt1, *(8, 0))

        return

    def close(self):
        Parent = self.parent().parent()
        self.setParent(None)

        Parent.LoginWin.textboxLogin.clear()
        Parent.LoginWin.textboxPassword.clear()

        Parent.layout.addWidget(Parent.LoginWin, *(1, 1, 1, 1))


class ChangePasswordWindow(QMainWindow):
    def __init__(self):
        super(ChangePasswordWindow, self).__init__()

        self.setGeometry(300, 300, 600, 600)
        self.setWindowTitle("Change password")
        self.setWindowIcon(QIcon("iconChangePassword.jpg"))

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.loginWin = ChangePasswordWidget(self)
        self.loginWin.setFixedSize(500, 250)
        self.layout.addWidget(self.loginWin, *(1, 1, 1, 1))

        self.show()

        return


class ChangePasswordWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)
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

        CurrentPassword = self.textboxCurrentPassword.text()
        NewPassword = self.textboxNewPassword.text()
        ConfirmedPassword = self.textboxConfirmedPassword.text()

        data = {"CurrentPassword": CurrentPassword, "NewPassword": NewPassword, "ConfirmedPassword": ConfirmedPassword}
        s.send(str.encode(str(data)))
        answer = s.recv(BUFFER_SIZE)
        QMessageBox.about(self, "Information", answer.decode())
        Parent = self.parent().parent()
        Parent.close()


class DataWindow(QMainWindow):
    def __init__(self, data):
        super(DataWindow, self).__init__()

        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle("Account data")

        self.frame = QFrame(self)
        self.layout = QGridLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        for count, key in enumerate(data):
            self.label = QLabel(str(key) + ": " + str(data[key]))
            self.label.setFont(QFont('Arial', 10))
            self.label.setAlignment(Qt.AlignLeft)
            self.layout.addWidget(self.label, *(count, 0, 1, 1))


        self.show



if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Plastique'))
    myGUI = MainWindow()
    sys.exit(app.exec_())
