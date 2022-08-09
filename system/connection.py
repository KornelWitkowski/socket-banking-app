import socket
from multiprocessing import Process

from utils import check_dict

from Communicates import Communicates
from DatabaseConnection import DatabaseProcessRequest
from Connection import ConnectionService

TCP_IP = '127.0.0.1'


class SystemConnectionService(ConnectionService):
    def __init__(self, address, connection):
        super().__init__(connection)
        self.logged_in = False
        self.user_id = None
        self.connection_id = None
        self.address = address
        self.database = DatabaseProcessRequest()

    def service_login_process(self, login_dict):
        login_dict = check_dict(login_dict, ['Login', 'Password'])

        if login_dict is None:
            return Communicates.ERROR

        row_values = self.database.get_row_with_given_login(login_dict['Login'])

        if not row_values:
            return Communicates.WRONG_LOGIN

        self.user_id = row_values[0][0]     # data is in the form [(id, ..., ...)]
        account_data = self.get_account_data_dict()

        if account_data["status"] == 0:
            return Communicates.ACCOUNT_BLOCKED
        if account_data["activity"] == 1:
            return Communicates.ACCOUNT_IN_USE
        if account_data["password"] != login_dict['Password']:
            if account_data["attempts"] + 1 >= 5:       # the maximal allowed number of login attempts is 5
                self.database.block_account(account_data["ID"])
                return Communicates.ACCOUNT_HAS_BEEN_BLOCKED
            self.database.increment_attempts(account_data["ID"])
            return Communicates.WRONG_PASSWORD
        # if login and password are correct then log in
        self.connection_id = self.database.assign_as_logged_in(self.address, account_data)
        self.logged_in = True
        self.user_id = account_data["ID"]

        return Communicates.LOGGED_IN

    def get_account_data_dict(self):
        return self.database.get_account_data_dict(self.user_id)

    def send_account_data_dict(self):
        account_data_dict = self.get_account_data_dict()
        self.send_dict(account_data_dict)
        return

    def service_logout(self):
        self.database.assign_as_logged_out(self.user_id, self.connection_id)
        self.logged_in = False
        self.user_id = None
        self.connection_id = None
        return

    def block_account(self):
        self.database.block_account(self.user_id)
        self.service_logout()
        self.send_communicate(Communicates.ACCOUNT_HAS_BEEN_BLOCKED)
        return

    def service_payment(self):
        payment_dict = check_dict(self.request_dict(), ['transaction type', 'amount', 'transaction time'])

        if payment_dict is None:
            return

        self.database.set_payment_down(self.user_id, payment_dict)
        self.send_dict({'balance': self.get_account_data_dict()['balance']})

        return

    def service_password_change(self):
        change_password_dict = check_dict(self.request_dict(), ["CurrentPassword", "NewPassword", "ConfirmedPassword"])
        account_data = self.get_account_data_dict()

        if change_password_dict["CurrentPassword"] == account_data["password"]:
            if change_password_dict['NewPassword'] == account_data["password"]:
                return Communicates.OLD_AND_NEW_PASSWORD_ARE_THE_SAME
            if change_password_dict['NewPassword'] != change_password_dict['ConfirmedPassword']:
                return Communicates.PASSWORDS_ARE_DIFFERENT

            self.database.update_password(self.user_id, change_password_dict['NewPassword'])
            return Communicates.PASSWORD_CHANGED

        return Communicates.WRONG_PASSWORD

    def send_history(self):
        history = self.database.get_history(self.user_id)
        self.connection.send(str.encode(history))
        return


def process_request(connection, address):

    with connection:
        connection_service = SystemConnectionService(address, connection)

        while True:
            data = connection_service.receive_message()
            if data is None:
                connection_service.service_logout()
                break

            if not connection_service.logged_in:
                communicate = connection_service.service_login_process(data)
                connection_service.send_communicate(communicate)

            if connection_service.logged_in:

                if data == Communicates.GIVE_ACCOUNT_DATA.value:
                    connection_service.send_account_data_dict()

                if data == Communicates.LOGOUT.value:
                    connection_service.service_logout()

                if data == Communicates.BLOCK_ACCOUNT.value:
                    connection_service.block_account()

                if data == Communicates.PAYMENT.value:
                    connection_service.service_payment()

                if data == Communicates.GIVE_HISTORY.value:
                    connection_service.send_history()

                if data == Communicates.CHANGE_PASSWORD.value:
                    communicate = connection_service.service_password_change()
                    connection_service.send_communicate(communicate)

        connection.close()


def process_socket(tcp_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((TCP_IP, tcp_port))
        sock.listen()
        processes = []

        while True:
            connection, address = sock.accept()
            p = Process(target=process_request, args=(connection, address))
            processes.append(p)
            p.start()
            for p in processes:
                p.join()
