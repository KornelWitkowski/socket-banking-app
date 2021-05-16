import sqlite3

import socket
import sys
import ast

from multiprocessing import Process

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


conSQL = sqlite3.connect('Database.db')
cur = conSQL.cursor()
cur.execute('''UPDATE Connections SET activity = 0''')
cur.execute('''UPDATE ClientData SET activity = 0''')
conSQL.commit()

TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024


def process_request(conn, addr):
    print('connected client:', addr)

    with conn:

        loggedIn = False
        UserId = None

        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
            except:
                break

            if not data:
                if loggedIn:
                    cur.execute('''UPDATE ClientData SET activity = ? where ID = ?''', (False, UserId))
                    if Time:
                        cur.execute('''UPDATE Connections SET activity = ?
                                                where time = ?''', (False, Time))
                    conSQL.commit()
                break

            if not loggedIn:

                try:
                    DecodedData = ast.literal_eval(data.decode())
                except:
                    conn.send(b"Not ok")
                    continue

                AccountData = []

                for row in cur.execute("SELECT * FROM ClientData WHERE login = '%s'" % DecodedData["Login"]):
                    AccountData.append(row)

                if len(AccountData) == 0:
                    conn.send(b"Not ok")
                else:
                    if AccountData[0][5] == DecodedData["Password"]:
                        conn.send(b"Ok")
                        cur.execute('''UPDATE ClientData SET activity = ?, attempts = ?
                        where login = ?''', (True, 0, DecodedData["Login"]))
                        loggedIn = True

                        Time = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')

                        cur.execute("INSERT INTO Connections (ip, port, user, time, activity )"
                                    " values (?, ?, ?, ?, ?)",
                                    (str(addr[0]), addr[1], AccountData[0][1] + " " + AccountData[0][2],
                                     Time,  1))

                        conSQL.commit()



                    else:
                        cur.execute('''UPDATE ClientData SET attempts = ? where login = ?''',
                                    (AccountData[0][8] + 1, DecodedData["Login"]))
                        if AccountData[0][8] + 1 >= 5:
                            cur.execute('''UPDATE ClientData SET status = ? where login = ?''',
                                        (False, DecodedData["Login"]))
                        conSQL.commit()
                        conn.send(b"Not ok")

            else:

                AccountData = []

                if data.decode() == 'Give me all that you got now!':

                    for row in cur.execute("SELECT * FROM ClientData WHERE login = '%s'" % DecodedData["Login"]):
                        for cell in row:
                            AccountData.append(cell)

                    AccountDataDic = {"id": AccountData[0], "name": AccountData[1], "surname": AccountData[2],
                                   "PESEL": AccountData[3], "login": AccountData[4], "password": AccountData[5],
                                   "balance": AccountData[6], "status": AccountData[7]}

                    UserId = AccountData[0]

                    conn.send(str.encode(str(AccountDataDic)))

                elif data.decode() == 'Logout':
                    cur.execute('''UPDATE ClientData SET activity = ? where ID = ?''', (False, UserId))
                    if Time:
                        cur.execute('''UPDATE Connections SET activity = ?
                                                where time = ?''', (False, Time))
                    conSQL.commit()
                    loggedIn = False

                elif data.decode() == 'Block account':
                    cur.execute('''UPDATE ClientData SET status = ? activity = ?  where ID = ?''', (False, False, UserId))
                    conSQL.commit()
                    conn.send(str.encode(str("Account has been blocked")))

                elif data.decode() == 'Show data':
                    for row in cur.execute("SELECT * FROM ClientData WHERE login = '%s'" % DecodedData["Login"]):
                        for cell in row:
                            AccountData.append(cell)

                    AccountDataDic = {"id": AccountData[0], "name": AccountData[1], "surname": AccountData[2],
                                   "PESEL": AccountData[3], "login": AccountData[4], "password": AccountData[5],
                                   "balance": AccountData[6], "status": AccountData[7]}

                    conn.send(str.encode(str(AccountDataDic)))

                try:
                    DecodedData = ast.literal_eval(data.decode())
                    AccountData = []

                    for row in cur.execute("SELECT * FROM ClientData WHERE ID = '%s'" % UserId):
                        for cell in row:
                            AccountData.append(cell)

                    AccountDataDic = {"id": AccountData[0], "name": AccountData[1], "surname": AccountData[2],
                                      "PESEL": AccountData[3], "login": AccountData[4], "password": AccountData[5],
                                      "balance": AccountData[6], "status": AccountData[7]}
                except:
                    continue

                if 'transaction type' in DecodedData:

                    transactionType = DecodedData['transaction type']
                    amount = int(DecodedData['amount'])
                    transactionTime = DecodedData['transaction time']

                    if DecodedData['transaction type'] == "Deposit" or DecodedData['transaction type'] == "Payout":


                        balance = AccountData[6]

                        if transactionType == "Deposit":
                            cur.execute('''UPDATE ClientData SET balance = ? where ID = ?''', (balance + amount, UserId))
                            conSQL.commit()
                            conn.send(str.encode(str({'balance': balance + amount})))
                        else:
                            if balance >= amount:
                                cur.execute('''UPDATE ClientData SET balance = ? where ID = ?''', (balance - amount, UserId))
                                conSQL.commit()
                                conn.send(str.encode(str({'balance': balance - amount})))
                            else:

                                conn.send(str.encode("Not enough money."))

                elif 'CurrentPassword' in DecodedData:

                    if DecodedData['CurrentPassword'] == AccountDataDic['password']:
                        if DecodedData['CurrentPassword'] == DecodedData['NewPassword']:
                            conn.send(str.encode("Current and new passwords are the same."))
                        elif DecodedData['NewPassword'] != DecodedData['ConfirmedPassword']:
                            conn.send(str.encode("Passwords are different."))
                        else:
                            cur.execute('''UPDATE ClientData SET password = ? where ID = ?''',
                                        (DecodedData['NewPassword'], UserId))
                            conSQL.commit()
                            conn.send(str.encode("Password has been changed."))
                    else:
                        conn.send(str.encode("Invalid password."))

        conn.close()


def process_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((TCP_IP, TCP_PORT))
        sock.listen()
        processes = []
        while True:
            conn, addr = sock.accept()
            p = Process(target=process_request, args=(conn, addr))
            processes.append(p)
            print('starting new process')
            p.start()
            for p in processes:
                p.join()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setGeometry(300, 300, 1200, 800)
        self.setWindowTitle("System")
        self.setWindowIcon(QIcon("iconSystem.jpg"))
        self.x = 2

        self.frame = QFrame(self)
        self.LAYOUT = QGridLayout()
        self.frame.setLayout(self.LAYOUT)
        self.setCentralWidget(self.frame)

        self.addRecordWidget = AddRecordWidget(self)
        self.addRecordWidget.setFixedSize(500, 250)
        self.LAYOUT.addWidget(self.addRecordWidget, *(2, 1, 1, 1))

        self.showDatabaseWidget = ShowDatabaseWidget(self)
        self.showDatabaseWidget.setFixedSize(1420, 500)
        self.LAYOUT.addWidget(self.showDatabaseWidget, *(1, 0, 1, 4))

        self.connectionTable = ConnectionTable(self)
        self.connectionTable.setFixedSize(580, 300)
        self.LAYOUT.addWidget(self.connectionTable, *(2, 0, 1, 1))

        self.show()
        return


class ConnectionTable(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        self.lay = QGridLayout(self)

        rowNumber = len(cur.fetchall())
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(rowNumber)
        columnNumber = 4
        self.tableWidget.setColumnCount(columnNumber)
        self.tableWidget.setHorizontalHeaderLabels(["IP", "Port", "User", "Time"])

        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        for count1, row in enumerate(cur.execute('SELECT * FROM Connections Where activity = 1')):
            for count2, cell in enumerate(row):
                if count2 == 0:
                    continue
                self.tableWidget.setItem(count1, count2-1, QTableWidgetItem(str(cell)))

        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))

        p = Process(target=process_socket)
        p.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        return

    def refresh(self):

        cur.execute('SELECT * FROM Connections where activity = 1')
        rowNumber = len(cur.fetchall())
        self.tableWidget.setRowCount(rowNumber)

        for count1, row in enumerate(cur.execute('SELECT * FROM Connections Where activity = 1')):
            for count2, cell in enumerate(row):
                if count2 == 0:
                    continue
                self.tableWidget.setItem(count1, count2-1, QTableWidgetItem(str(cell)))

        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))

        return


class AddRecordWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        self.lay = QGridLayout(self)

        labels = {(1, 0): "Imię:", (2, 0): "Nazwisko:",
                    (3, 0): "PESEL:", (4, 0): "Login:", (5, 0): "Hasło:",
                    (6, 0): "Saldo:", (7, 0): "Stan konta:"}

        for pos, name in labels.items():
            x, y = pos
            label = QLabel()
            label.setText(name)
            label.setAlignment(Qt.AlignRight)
            self.lay.addWidget(label, x, y)

        self.textboxName = QLineEdit(self)
        self.textboxName.setFixedSize(150, 20)
        self.lay.addWidget(self.textboxName, *(1, 1, 1, 1))

        self.textboxSurname = QLineEdit(self)
        self.textboxSurname.setFixedSize(150, 20)
        self.lay.addWidget(self.textboxSurname, *(2, 1, 1, 1))

        self.textboxPESEL = QLineEdit(self)
        self.textboxPESEL.setFixedSize(150, 20)
        self.lay.addWidget(self.textboxPESEL, *(3, 1, 1, 1))

        self.textboxLogin = QLineEdit(self)
        self.textboxLogin.setFixedSize(150, 20)
        self.lay.addWidget(self.textboxLogin, *(4, 1, 1, 1))

        self.textboxPassword = QLineEdit(self)
        self.textboxPassword.setFixedSize(150, 20)
        self.lay.addWidget(self.textboxPassword, *(5, 1, 1, 1))

        self.textboxBalance = QLineEdit(self)
        self.textboxBalance.setFixedSize(150, 20)
        self.lay.addWidget(self.textboxBalance, *(6, 1, 1, 1))

        self.selectStatus = QComboBox(self)
        self.selectStatus.setFixedSize(150, 20)
        self.selectStatus.addItem("Aktywne")
        self.selectStatus.addItem("Zablokowane")
        self.lay.addWidget(self.selectStatus, *(7, 1, 1, 1))

        self.newRecordButton = QPushButton(self, text="Dodaj")
        self.newRecordButton.setFixedSize(150, 40)
        self.newRecordButton.clicked.connect(self.add_new_record)
        self.lay.addWidget(self.newRecordButton, *(8, 1, 1, 1))

        self.setLayout(self.lay)
        return

    def add_new_record(self):

        Parent = self.parent().parent()

        name = self.textboxName.text()
        surname = self.textboxSurname.text()
        PESEL = self.textboxPESEL.text()
        login = self.textboxLogin.text()
        password = self.textboxPassword.text()
        balance = self.textboxBalance.text()
        status = self.selectStatus.currentText() == "Aktywne"

        if len(name) == 0 or len(surname) == 0 or len(PESEL) == 0 or len(login) == 0 \
                or len(password) == 0 or len(balance) == 0:
            QMessageBox.about(Parent, "Błąd", "Pola nie mogą być puste.")
            return
        elif not name.isalpha() or not surname.isalpha():
            QMessageBox.about(Parent, "Błąd", "Błędny typ danych.")
            return

        try:
            int(PESEL)
            float(balance)
        except:
            QMessageBox.about(Parent, "Błąd", "Błędny typ danych.")
            return

        cur.execute("INSERT INTO ClientData (name, surname, PESEL, login, password, balance, status)"
                    " values (?, ?, ?, ?, ?, ?, ?)",
                    (name.title(), surname.title(), int(PESEL), login, password, int(balance), status))
        conSQL.commit()

        Parent.showDatabaseWidget.refresh()

        return


class ShowDatabaseWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        self.lay = QGridLayout(self)
        self.sortingParameter = False
        self.sortingStatus = False

        cur.execute('SELECT * FROM ClientData')
        rowNumber = len(cur.fetchall())

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(rowNumber)
        self.tableWidget.setColumnCount(11)

        self.tableWidget.setHorizontalHeaderLabels(["Imię", "Nazwisko", "PESEL", "Login", "Hasło",
                                                    "Saldo", "Status", "Liczba prób", "Aktywność", "", ""])

        for count1, row in enumerate(cur.execute("SELECT * FROM ClientData ORDER BY name ")):
            for count2, cell in enumerate(row):
                if count2 == 0:
                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText('Usuń')
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(count1, 9, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('Historia')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(count1, 10, historyBtn)
                else:
                    self.tableWidget.setItem(count1, count2 - 1, QTableWidgetItem(str(cell)))

        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.database_header_clicked)

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.refresh(autorefresh=True))
        self.timer.start(1000)

        return

    def show_history(self):

        # tu w przyszłości powinno być okienko, które pokaże historie; delete_record poniżej może trochę pomóc
        return

    def delete_record(self):

        try:
            sending_button = self.sender()
            record_id = int(sending_button.objectName())
            cur.execute('DELETE FROM ClientData WHERE id=?', (record_id,))
            conSQL.commit()
            self.refresh()
            return
        except:
            return

    def database_header_clicked(self, header_number):

            if header_number > 7:
                return
            else:
                self.sortingParameter = header_number
                self.refresh()
                return

    def refresh(self, **kwargs):
        autorefresh = kwargs.get('autorefresh', False)

        cur.execute('SELECT * FROM ClientData')
        rowNumber = len(cur.fetchall())
        self.tableWidget.setRowCount(rowNumber)

        if not self.sortingStatus:
            databaseTable = cur.execute("SELECT * FROM ClientData ORDER BY {}".format(self.sortingParameter+2))
            if not autorefresh:
                self.sortingStatus = True
        else:
            databaseTable = cur.execute("SELECT * FROM ClientData ORDER BY {} DESC".format(self.sortingParameter+2))
            if not autorefresh:
                self.sortingStatus = False

        for count1, row in enumerate(databaseTable):
            for count2, cell in enumerate(row):
                self.tableWidget.setItem(count1, count2 - 1, QTableWidgetItem(str(cell)))

                if count2 == 0:
                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText("Usuń")
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(count1, 9, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('Historia')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(count1, 10, historyBtn)

        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Plastique'))
    myGUI = MainWindow()
    sys.exit(app.exec_())
