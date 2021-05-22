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
#TCP_PORT = 5005
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
                if Time:
                    cur.execute('''UPDATE Connections SET activity = ?
                                            where time = ?''', (False, Time))
                conSQL.commit()
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
                    conn.send(b"Wrong login")
                else:

                    if AccountData[0][9] == 0:
                        conn.send(b"Account blocked")
                    elif AccountData[0][8] == 1:
                        conn.send(b"Account in use")
                    elif AccountData[0][5] == DecodedData["Password"]:
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
                        print(AccountData[0][8])
                        cur.execute('''UPDATE ClientData SET attempts = ? where login = ?''',
                                    (AccountData[0][7] + 1, DecodedData["Login"]))

                        if AccountData[0][7] + 1 >= 5:
                            cur.execute('''UPDATE ClientData SET status = ? where login = ?''',
                                        (False, DecodedData["Login"]))
                            conSQL.commit()
                            conn.send(b"Account has been blocked")
                        else:
                            conSQL.commit()
                            conn.send(b"Wrong password")

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
                    cur.execute('''UPDATE ClientData SET status = ?, activity = ?  where ID = ?''', (False, False, UserId))
                    conSQL.commit()
                    conn.send(str.encode(str("Account has been blocked")))

                elif data.decode() == "History":
                    cur.execute('SELECT history FROM  ClientData WHERE id=?', (UserId,))
                    history = cur.fetchone()[0]
                    conn.send(str.encode(history))

                elif data.decode() == 'Show data':
                    for row in cur.execute("SELECT * FROM ClientData WHERE id = '%s'" % UserId):
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
                            cur.execute('SELECT history FROM ClientData where id =?', (UserId,))
                            history = cur.fetchone()[0]
                            if history == ' ':
                                cur.execute('''UPDATE ClientData SET history = ? where ID = ?''',
                                            (transactionType + " " + str(amount) + " "
                                             + transactionTime, UserId))
                            else:
                                cur.execute('''UPDATE ClientData SET history = ? where ID = ?''',
                                            (history + "\n" + transactionType + " " + str(amount) + " "
                                             + transactionTime, UserId))

                            conSQL.commit()
                            conn.send(str.encode(str({'balance': balance + amount})))
                        else:
                            if balance >= amount:
                                cur.execute('''UPDATE ClientData SET balance = ? where ID = ?''', (balance - amount, UserId))
                                cur.execute('SELECT history FROM ClientData where id =?', (UserId,))
                                history = cur.fetchone()[0]
                                if history == ' ':
                                    cur.execute('''UPDATE ClientData SET history = ? where ID = ?''',
                                                (transactionType + " " + str(amount) + " "
                                                 + transactionTime , UserId))
                                else:
                                    cur.execute('''UPDATE ClientData SET history = ? where ID = ?''',
                                                (history + "\n" + transactionType + " " + str(amount) + " "
                                                 + transactionTime, UserId))

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


def process_socket(TCP_PORT):
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

        self.showDatabaseWidget = ShowDatabaseWidget(self)
        self.showDatabaseWidget.setFixedSize(1420, 500)
        self.LAYOUT.addWidget(self.showDatabaseWidget, *(1, 0, 1, 6))

        self.connectionTable = ConnectionTable(self)
        self.connectionTable.setFixedSize(580, 300)
        self.LAYOUT.addWidget(self.connectionTable, *(2, 0, 1, 1))

        self.addRecordWidget = AddRecordWidget(self)
        self.addRecordWidget.setFixedSize(300, 300)
        self.LAYOUT.addWidget(self.addRecordWidget, *(2, 2, 1, 1))

        self.showHistoryWidget = ShowHistoryWidget(self)
        self.showHistoryWidget.setFixedSize(500, 300)
        self.LAYOUT.addWidget(self.showHistoryWidget, *(2, 1, 1, 1))

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
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        for count1, row in enumerate(cur.execute('SELECT * FROM Connections Where activity = 1')):
            for count2, cell in enumerate(row):
                if count2 == 0:
                    continue
                self.tableWidget.setItem(count1, count2-1, QTableWidgetItem(str(cell)))

        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))

        for i in range(5):
            p = Process(target=process_socket, args=(5005+1000*i,))
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

        labels = {(1, 0): "Name:", (2, 0): "Surname:",
                    (3, 0): "PESEL:", (4, 0): "Login:", (5, 0): "Password:",
                    (6, 0): "Balance:", (7, 0): "Status:"}

        for pos, name in labels.items():
            x, y = pos
            label = QLabel()
            label.setText(name)
            label.setAlignment(Qt.AlignRight)
            label.setFont(QFont('Arial', 10))
            self.lay.addWidget(label, x, y)

        self.textboxName = QLineEdit(self)
        self.textboxName.setFixedSize(150, 25)
        self.lay.addWidget(self.textboxName, *(1, 1, 1, 1))

        self.textboxSurname = QLineEdit(self)
        self.textboxSurname.setFixedSize(150, 25)
        self.lay.addWidget(self.textboxSurname, *(2, 1, 1, 1))

        self.textboxPESEL = QLineEdit(self)
        self.textboxPESEL.setFixedSize(150, 25)
        self.lay.addWidget(self.textboxPESEL, *(3, 1, 1, 1))

        self.textboxLogin = QLineEdit(self)
        self.textboxLogin.setFixedSize(150, 25)
        self.lay.addWidget(self.textboxLogin, *(4, 1, 1, 1))

        self.textboxPassword = QLineEdit(self)
        self.textboxPassword.setFixedSize(150, 25)
        self.lay.addWidget(self.textboxPassword, *(5, 1, 1, 1))

        self.textboxBalance = QLineEdit(self)
        self.textboxBalance.setFixedSize(150, 25)
        self.lay.addWidget(self.textboxBalance, *(6, 1, 1, 1))

        self.selectStatus = QComboBox(self)
        self.selectStatus.setFixedSize(150, 25)
        self.selectStatus.addItem("Active")
        self.selectStatus.addItem("Block")
        self.lay.addWidget(self.selectStatus, *(7, 1, 1, 1))

        self.newRecordButton = QPushButton(self, text="Add")
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
        status = self.selectStatus.currentText() == "Active"

        if len(name) == 0 or len(surname) == 0 or len(PESEL) == 0 or len(login) == 0 \
                or len(password) == 0 or len(balance) == 0:
            QMessageBox.about(Parent, "Error", "Field can not be empty.")
            return
        elif not name.isalpha() or not surname.isalpha():
            QMessageBox.about(Parent, "Error", "Invalid data.")
            return

        try:
            int(PESEL)
            float(balance)
        except:
            QMessageBox.about(Parent, "Error", "Invalid data.")
            return

        cur.execute("""SELECT * FROM ClientData where login = ?""", (login,))

        if cur.fetchone():
            QMessageBox.about(Parent, "Error", "Login already taken.")
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

        self.tableWidget.setHorizontalHeaderLabels(["Name", "Surname", "PESEL", "Login", "Password",
                                                    "Balance", "Attempts", "Activity", "Status", "", ""])

        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        for count1, row in enumerate(cur.execute("SELECT id, name, surname, pesel, login, password, balance,"
                                                 " attempts, activity, status FROM ClientData ORDER BY name ")):
            for count2, cell in enumerate(row):
                if count2 == 0:

                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText('Delete')
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(count1, 9, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('History')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(count1, 10, historyBtn)

                elif count2 == 9:

                    statusBtn = QPushButton(self.tableWidget)
                    statusBtn.setText(str(cell))
                    statusBtn.setObjectName(str(row[0]))
                    statusBtn.clicked.connect(self.change_status)
                    self.tableWidget.setCellWidget(count1, 8, statusBtn)

                elif count2 == 10:

                    continue

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

        sending_button = self.sender()
        record_id = int(sending_button.objectName())
        cur.execute('SELECT history FROM  ClientData WHERE id=?', (record_id,))
        history = cur.fetchone()[0]

        list1 = []
        list2 = history.split('\n')

        for row in list2:
            list1.append(row.split(' '))

        Parent = self.parent().parent()
        Parent.showHistoryWidget.refresh(list1)

        return

    def change_status(self):

        try:
            sending_button = self.sender()
            record_id = int(sending_button.objectName())
            cur.execute('SELECT status FROM ClientData where id =?', (record_id,))
            status = cur.fetchone()[0]
            cur.execute('UPDATE ClientData SET status = ?, attempts = ? WHERE id=?', (not bool(status), 0, record_id))
            conSQL.commit()
            self.refresh()
            return
        except:
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
                self.refresh(sort=True)
                return

    def refresh(self, **kwargs):
        autorefresh = kwargs.get('autorefresh', False)
        sort = kwargs.get('sort', False)

        cur.execute('SELECT * FROM ClientData')
        rowNumber = len(cur.fetchall())
        self.tableWidget.setRowCount(rowNumber)

        if not autorefresh and sort:
            self.sortingStatus = not self.sortingStatus

        if not self.sortingStatus:
            databaseTable = cur.execute("SELECT * FROM ClientData ORDER BY {}".format(self.sortingParameter+2))
        else:
            databaseTable = cur.execute("SELECT * FROM ClientData ORDER BY {} DESC".format(self.sortingParameter+2))

        self.tableWidget.setParent(None)

        for count1, row in enumerate(databaseTable):
            for count2, cell in enumerate(row):

                if count2 == 0:

                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText("Delete")
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(count1, 9, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('History')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(count1, 10, historyBtn)

                elif count2 == 9:
                    statusBtn = QPushButton(self.tableWidget)
                    statusBtn.setText(str(cell))
                    statusBtn.setObjectName(str(row[0]))
                    statusBtn.clicked.connect(self.change_status)
                    self.tableWidget.setCellWidget(count1, 8, statusBtn)

                elif count2 == 10:
                    continue

                else:
                    self.tableWidget.setItem(count1, count2 - 1, QTableWidgetItem(str(cell)))

        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))
        return


class ShowHistoryWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        self.lay = QGridLayout(self)

        cur.execute('SELECT * FROM ClientData')

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setHorizontalHeaderLabels(["Type", "Amount", "Time"])

        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))

    def refresh(self, data):

        if data == [['', '']]:
            self.tableWidget.setRowCount(0)
        else:
            self.tableWidget.setRowCount(len(data))

        for count1, row in enumerate(data):
            for count2, cell in enumerate(row):
                if count2 < 2:
                    self.tableWidget.setItem(count1, count2, QTableWidgetItem(str(cell)))
                elif count2 == 2:
                    self.tableWidget.setItem(count1, count2, QTableWidgetItem(str(cell) + " "+ str(row[3])))
                else:
                    continue
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Plastique'))
    myGUI = MainWindow()
    sys.exit(app.exec_())
