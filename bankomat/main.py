import sys
import socket
import time

import time as Time

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

        # Create window
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Cash machine")
        self.setWindowIcon(QIcon("icon.jpg"))

        # Create FRAME_A
        self.FRAME = QFrame(self)
        self.LAYOUT = QGridLayout()
        self.FRAME.setLayout(self.LAYOUT)
        self.setCentralWidget(self.FRAME)

        self.loginWin = loginWindow(self)
        self.loginWin.setFixedSize(500, 250)
        self.LAYOUT.addWidget(self.loginWin, *(1, 1, 1, 1))

        self.show()
        return


class loginWindow(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)
        lay = QGridLayout(self)

        self.labelName = QLabel("Login:")
        self.labelName.setFont(QFont('Arial', 14))
        self.labelName.setAlignment(Qt.AlignLeft)
        lay.addWidget(self.labelName, *(1, 0, 1, 1))
        self.textboxName=QLineEdit(self)
        self.textboxName.setFont(QFont('Arial', 14))
        self.textboxName.setFixedSize(200, 50)
        lay.addWidget(self.textboxName, *(2, 0, 1, 1))

        self.labelPassword = QLabel("Password:")
        self.labelPassword.setFont(QFont('Arial', 14))
        self.labelPassword.setAlignment(Qt.AlignLeft)
        lay.addWidget(self.labelPassword, *(3, 0, 1, 1))
        self.textboxPassword = QLineEdit(self)
        self.textboxPassword.setEchoMode(QLineEdit.Password)
        self.textboxPassword.setFont(QFont('Arial', 14))
        self.textboxPassword.setFixedSize(200, 50)
        lay.addWidget(self.textboxPassword, *(4, 0, 1, 1))

        self.setBtn = QPushButton(text='Log in')
        self.setBtn.setFont(QFont('Arial', 14))
        self.setBtn.setFixedSize(200, 45)
        self.setBtn.clicked.connect(self.logInBtn)
        lay.addWidget(self.setBtn, *(5, 0))

        return

    def logInBtn(self):

        Name = self.textboxName.text()
        Password = self.textboxPassword.text()
        data = {"Login": Name, "Password" : Password}
        s.send(str.encode(str(data)))
        answer = s.recv(BUFFER_SIZE)
        #print()

        Parent = self.parent().parent()

      #  if answer.decode() =="Ok":
        self.setParent(None)
        Parent.loggedinWin = loggedinWindow(self)
        Parent.loggedinWin.setFixedSize(500, 250)
        Parent.LAYOUT.addWidget(Parent.loggedinWin, *(1, 1, 1, 1))


class loggedinWindow(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        time.sleep(0.5)
        s.send(str.encode("Give me all that you got now!"))
        answer = s.recv(BUFFER_SIZE)

        #DecodedData = ast.literal_eval(answer.decode()) Czemu to nie działa?
        json_acceptable_string = answer.decode().replace("'", "\"")
        Data = json.loads(json_acceptable_string)


        self.lay = QGridLayout(self)
        self.labelTime = QLabel(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss dddd'))
        self.timer = QTimer()
        self.timer.timeout.connect(self.showTime)
        self.lay.addWidget(self.labelTime, 0, 1, 1, 2)
        self.timer.start(1000)

        self.labelName = QLabel(Data["name"] + " " + Data["surname"])
        self.lay.addWidget(self.labelName, 1, 1, 1, 2)

        self.labelBalance = QLabel("Balance:  " + str(Data["balance"]))
        self.lay.addWidget(self.labelBalance, 2, 1, 1, 2)

        self.textboxTimeMax = QLineEdit(self)
        self.textboxTimeMax.setFixedSize(100, 25)
        self.lay.addWidget(self.textboxTimeMax, *(3, 1, 1, 1))

        btns = {(4, 0): "Payment", (4, 1): "Payoff",
                (5, 0): "History", (5, 1): "Data",
                (6, 0): "Change password", (6, 1): "Block account"}


        for pos, name in btns.items():
            x, y = pos
            btn = QPushButton()
            btn.setText(name)
            self.lay.addWidget(btn, x, y)

        self.setBtn = QPushButton(text='Log out')
        self.setBtn.setFont(QFont('Arial', 14))
        self.setBtn.setFixedSize(200, 45)
        self.setBtn.clicked.connect(self.wylogowanie)
        self.lay.addWidget(self.setBtn, *(8, 0))


    def showTime(self):
        time = QDateTime.currentDateTime()
        timeDisplay = time.toString('yyyy-MM-dd hh:mm:ss dddd')
        self.labelTime.setText(timeDisplay)

    def wylogowanie(self):
        Parent = self.parent().parent()
        self.setParent(None)
        Parent.logout = Ekran_wylogowania(self)
        Parent.logout.setFixedSize(500, 250)
        Parent.LAYOUT.addWidget(Parent.logout, *(1, 1, 1, 1))

class Ekran_wylogowania(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)
        lay = QGridLayout(self)

        self.labelName = QLabel("Zostałeś poprawnie wylogowany! :)")
        self.labelName.setFont(QFont('Arial', 14))
        self.labelName.setAlignment(Qt.AlignLeft)
        lay.addWidget(self.labelName, *(1, 0))


        self.bt1 = QPushButton(text='Zamknij')
        self.bt1.setFont(QFont('Arial', 14))
        self.bt1.setFixedSize(200, 45)
        self.bt1.clicked.connect(self.zamknij)
        lay.addWidget(self.bt1, *(8, 0))

#        self.bt2 = QPushButton(text='Zaloguj ponownie')
#        self.bt2.setFont(QFont('Arial', 14))
#        self.bt2.setFixedSize(200, 45)
#        self.bt2.clicked.connect(self.zaloguj_ponownie)
#        lay.addWidget(self.bt2, *(8, 1))

        return

    def zamknij(self):
        Parent = self.parent().parent()
        self.setParent(None)
        Parent.logout = exit()
        Parent.logout.setFixedSize(500, 250)
        Parent.LAYOUT.addWidget(Parent.logout, *(1, 1, 1, 1))

#    def zaloguj_ponownie(self):
#        Parent = self.parent().parent()
#        self.setParent(None)
#        Parent.log = loginWindow(self)
#        Parent.log.setFixedSize(500, 250)
#        Parent.LAYOUT.addWidget(Parent.log, *(1, 1, 1, 1))

if __name__== '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Plastique'))
    myGUI = MainWindow()
    sys.exit(app.exec_())