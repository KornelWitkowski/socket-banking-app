import sqlite3

import socket
import sys
import time
import ast

from multiprocessing import Process, Pipe

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


con = sqlite3.connect('Database.db')
cur = con.cursor()


TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 1024


def process_request(conn, addr):
    print('connected client:', addr)


    with conn:

        loggedIn = False
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
            except:
                break


            if not data: break


            if not loggedIn:

                try:
                    DecodedData = ast.literal_eval(data.decode())
                except:
                    conn.send(b"Not ok")
                    continue

                lista = []

                for row in cur.execute("SELECT * FROM ClientData WHERE login = '%s'" % DecodedData["Login"]):
                    lista.append(row)

                if len(lista) == 0:
                    conn.send(b"Not ok")
                else:
                    if lista[0][5] == DecodedData["Password"]:
                        conn.send(b"Ok")
                        loggedIn =True
                    else:
                        conn.send(b"Not ok")

            if loggedIn:
                lista = []

                for row in cur.execute("SELECT * FROM ClientData WHERE login = '%s'" % DecodedData["Login"]):
                    for cell in row:
                        lista.append(cell)

                lista = {"id": lista[0], "name": lista[1], "surname": lista[2], "PESEL": lista[3],
                         "login": lista[4], "password": lista[5], "balance": lista[6], "status": lista[7]}

                conn.send(str.encode(str(lista)))


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

        self.FRAME = QFrame(self)
        self.LAYOUT = QGridLayout()
        self.FRAME.setLayout(self.LAYOUT)
        self.setCentralWidget(self.FRAME)

        self.addRecordWidget = AddRecordWidget(self)
        self.addRecordWidget.setFixedSize(500, 250)
        self.LAYOUT.addWidget(self.addRecordWidget, *(1, 1, 1, 1))

        self.showDatabaseWidget = ShowDatabaseWidget(self)
        self.showDatabaseWidget.setFixedSize(1100, 500)
        self.LAYOUT.addWidget(self.showDatabaseWidget, *(1, 0, 1, 1))

        self.connectionTable = ConnectionTable(self)
        self.connectionTable.setFixedSize(1100, 300)
        self.LAYOUT.addWidget(self.showDatabaseWidget, *(5, 0, 1, 1))

        self.show()
        return


class ConnectionTable(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)

        self.lay = QGridLayout(self)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(5)
        self.tableWidget.setColumnCount(3)

        self.tableWidget.setHorizontalHeaderLabels(["Adres", "Status", "Użytkownik"])

        for i in range(5):
            for j in range(3):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(i)))

        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))
        #
        p = Process(target=process_socket)
        p.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        return

    def refresh(self):


        # for i in range(5):
        #     for j, adress in enumerate(connections_list):
        #         self.tableWidget.setItem(i, j, QTableWidgetItem(str(adress)))

        self.tableWidget.move(0, 0)
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

        self.selectActivity = QComboBox(self)
        self.selectActivity.setFixedSize(150, 20)
        self.selectActivity.addItem("Aktywne")
        self.selectActivity.addItem("Zablokowane")
        self.lay.addWidget(self.selectActivity, *(7, 1, 1, 1))

        self.newRecordButton = QPushButton(self, text="Dodaj")
        self.newRecordButton.setFixedSize(150, 40)
        self.newRecordButton.clicked.connect(self.addNewRecord)
        self.lay.addWidget(self.newRecordButton, *(8, 1, 1, 1))

        self.setLayout(self.lay)
        return

    def addNewRecord(self):

        Parent = self.parent().parent()

        name = self.textboxName.text()
        surname = self.textboxSurname.text()
        PESEL = self.textboxPESEL.text()
        login = self.textboxLogin.text()
        password = self.textboxPassword.text()
        balance = self.textboxBalance.text()
        activity = self.selectActivity.currentText() == "Aktywne"

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
            QMessageBox.about(self.Parent, "Błąd", "Błędny typ danych.")
            return

        cur.execute("INSERT INTO ClientData (name, surname, PESEL, login, password, balance, activity)"
                    " values (?, ?, ?, ?, ?, ?, ?)",
                    (name.title(), surname.title(), int(PESEL), login, password, int(balance), activity))
        con.commit()

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
        self.tableWidget.setColumnCount(9)

        self.tableWidget.setHorizontalHeaderLabels(["Imię", "Nazwisko", "PESEL", "Login", "Hasło",
                                                    "Saldo", "Status", "", ""])

        for count1, row in enumerate(cur.execute("SELECT * FROM ClientData ORDER BY name ")):
            for count2, cell in enumerate(row):
                if count2 == 0:
                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText('Usuń')
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(count1, 8, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('Historia')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(count1, 7, historyBtn)
                else:
                    self.tableWidget.setItem(count1, count2 - 1, QTableWidgetItem(str(cell)))


        self.tableWidget.move(0, 0)
        self.lay.addWidget(self.tableWidget,*(0, 0, 1, 1))
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.database_header_clicked)

        return

    def show_history(self):

        # tu w przyszłości powinno być okienko, które pokaże historie; delete_record poniżej może trochę pomóc
        return

    def delete_record(self):

        try:
            sending_button = self.sender()
            record_id = int(sending_button.objectName())
            sql = 'DELETE FROM ClientData WHERE id=?'
            cur.execute(sql, (record_id,))
            con.commit()
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

    def refresh(self):

        cur.execute('SELECT * FROM ClientData')
        rowNumber = len(cur.fetchall())
        self.tableWidget.setRowCount(rowNumber)

        if not self.sortingStatus:
            databaseTable = cur.execute("SELECT * FROM ClientData ORDER BY {}".format(self.sortingParameter+2))
            self.sortingStatus = True
        else:
            databaseTable = cur.execute("SELECT * FROM ClientData ORDER BY {} DESC".format(self.sortingParameter+2))
            self.sortingStatus = False

        for count1, row in enumerate(databaseTable):
            for count2, cell in enumerate(row):
                self.tableWidget.setItem(count1, count2 - 1, QTableWidgetItem(str(cell)))

                if count2 == 0:
                    deleteBtn = QPushButton(self.tableWidget)
                    deleteBtn.setText("Usuń")
                    deleteBtn.setObjectName(str(cell))
                    deleteBtn.clicked.connect(self.delete_record)
                    self.tableWidget.setCellWidget(count1, 8, deleteBtn)

                    historyBtn = QPushButton(self.tableWidget)
                    historyBtn.setText('Historia')
                    historyBtn.setObjectName(str(cell))
                    historyBtn.clicked.connect(self.show_history)
                    self.tableWidget.setCellWidget(count1, 7, historyBtn)

        self.lay.addWidget(self.tableWidget, *(0, 0, 1, 1))
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Plastique'))
    myGUI = MainWindow()
    sys.exit(app.exec_())
