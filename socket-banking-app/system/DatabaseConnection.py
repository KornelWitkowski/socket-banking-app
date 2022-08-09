from utils import get_integer

import sqlite3
import pandas as pd
from PyQt5.QtCore import QDateTime


class Database:
    DATABASE_NAME = 'Database.db'

    def __init__(self):
        self.connection_sql = sqlite3.connect(Database.DATABASE_NAME)
        self.cursor = self.connection_sql.cursor()

        # refresh activity records after previous closing
        self.cursor.execute('''UPDATE Connections SET activity = 0''')
        self.cursor.execute('''UPDATE ClientData SET activity = 0''')
        self.connection_sql.commit()

    def get_history(self, user_id):
        self.cursor.execute(f"SELECT history FROM  ClientData WHERE id = {user_id}")
        return self.cursor.fetchone()[0]


class DatabaseGUI(Database):
    def __init__(self):
        super().__init__()

    def get_active_connections_table(self):
        return self.cursor.execute('SELECT * FROM Connections WHERE activity = 1')

    def get_connections_row_number(self):
        _ = self.cursor.execute('SELECT activity FROM Connections where activity = 1')
        return len(self.cursor.fetchall())

    #   ClientData table functions

    def get_clientdata_df(self, sorting_parameter="name", sorting_status=False):
        sorting_order = " DESC" if sorting_status else ""
        return pd.read_sql(f"SELECT id, name, surname, phone, login, password, balance, attempts,"
                           f" activity, status FROM ClientData ORDER BY {sorting_parameter}{sorting_order}",
                           self.connection_sql)

    def get_clientdata_row_number(self):
        _ = self.cursor.execute('SELECT id FROM ClientData')
        return len(self.cursor.fetchall())

    def change_clientdata_status(self, record_id):
        record_id = get_integer(record_id)
        if not record_id:
            return
        self.cursor.execute('UPDATE ClientData SET status = NOT status, attempts = ? WHERE id=?',
                            (0, record_id))
        self.connection_sql.commit()
        return

    def delete_clientdata_row(self, record_id):
        record_id = get_integer(record_id)
        if not record_id:
            return
        self.cursor.execute('DELETE FROM ClientData WHERE id=?', (record_id,))
        self.connection_sql.commit()
        return

    def is_in_database(self, field, field_value):
        self.cursor.execute(f"""SELECT * FROM ClientData WHERE {field} = ?""", (field_value,))
        return self.cursor.fetchone()

    def insert_row_in_database(self, name, surname, phone, login, password, balance, status):

        self.cursor.execute("INSERT INTO ClientData (name, surname, phone, login, password, balance, status)"
                            " values (?, ?, ?, ?, ?, ?, ?)",
                            (name.title(), surname.title(), phone, login, password, balance, status))
        self.connection_sql.commit()
        return


class DatabaseProcessRequest(Database):
    def __init__(self):
        super().__init__()
        self.COLUMNS_NAMES = ["ID", "name", "surname", "phone", "login", "password",
                              "balance", "attempts", "activity", "status", "history"]

    def get_row_with_given_login(self, login):
        return list(self.cursor.execute(f"SELECT * FROM ClientData WHERE login = '{login}'"))

    def get_row_with_given_id(self, user_id):
        return list(self.cursor.execute(f"SELECT * FROM ClientData WHERE id = '{user_id}'"))[0]

    def block_account(self, user_id):
        self.cursor.execute(f"UPDATE ClientData SET status = 0, attempts = 0 WHERE id = {user_id}")
        self.connection_sql.commit()
        return

    def increment_attempts(self, user_id):
        self.cursor.execute(f"UPDATE ClientData SET attempts = attempts + 1 where ID = {user_id}")
        self.connection_sql.commit()
        return

    def assign_as_logged_in(self, address, account_data):
        user_id = account_data["ID"]
        self.cursor.execute(f"UPDATE ClientData SET activity = 1, attempts = 0 WHERE ID = {user_id}")

        ip, port = address
        user_name = f"{account_data['name']} {account_data['surname']}"
        time = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')

        self.cursor.execute(f"INSERT INTO Connections"
                            f" (ip, port, user, time, activity) VALUES ('{ip}', {port}, '{user_name}', '{time}', 1)")
        self.connection_sql.commit()

        return self.cursor.lastrowid    # it returns the id of a connection

    def assign_as_logged_out(self, user_id, connection_id):
        self.cursor.execute(f"UPDATE ClientData SET activity = 0 WHERE ID = {user_id}")
        self.cursor.execute(f"UPDATE Connections SET activity = 0 WHERE ID = {connection_id}")
        self.connection_sql.commit()
        return

    def get_account_data_dict(self, user_id):
        row_values = self.get_row_with_given_id(user_id)
        return dict(zip(self.COLUMNS_NAMES, row_values))

    def set_payment_down(self, user_id, payment_dict):
        amount = int(payment_dict["amount"])
        transaction_type = payment_dict["transaction type"]
        transaction_time = payment_dict["transaction time"]

        payment_history_entry = f"{transaction_type} {str(amount)} {transaction_time}\n"

        if transaction_type == "Payout":
            amount = - amount

        self.cursor.execute(f"UPDATE ClientData SET balance = balance + {amount} WHERE id = {user_id}")
        self.cursor.execute(f"UPDATE ClientData"
                            f" SET history =  history || '{payment_history_entry}' WHERE ID = {user_id}")
        self.connection_sql.commit()
        return

    def update_password(self, user_id, new_password):
        self.cursor.execute(f"UPDATE ClientData SET password = '{new_password}' WHERE id = {user_id}")
        self.connection_sql.commit()
        return
