from utils import decode_bytes
from Communicates import Communicates


class ConnectionService:
    BUFFER_SIZE = 10000

    def __init__(self, connection):
        self.connection = connection

    def send_communicate(self, communicate):
        self.connection.send(bytes(str(communicate.value), 'utf-8'))
        return

    def receive_message(self):
        try:
            message = self.connection.recv(ConnectionService.BUFFER_SIZE)
        except Exception:
            return None
        return decode_bytes(message)

    def send_dict(self, dictionary):
        self.connection.send(str.encode(str(dictionary)))
        return

    def request_dict(self):
        self.send_communicate(Communicates.SEND_DICT)
        return self.receive_message()
