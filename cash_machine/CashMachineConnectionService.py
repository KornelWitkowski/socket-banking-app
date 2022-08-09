from Connection import ConnectionService

class CashMachineConnectionService(ConnectionService):
    def __init__(self, connection):
        super().__init__(connection)

    def receive_string(self):
        return self.connection.recv(ConnectionService.BUFFER_SIZE).decode()

    def send_dict_and_receive_response(self, dictionary):
        self.send_dict(dictionary)
        return self.receive_message()

    def send_communicate_and_receive_response(self, communicate):
        self.send_communicate(communicate)
        return self.receive_message()

    def send_communicate_and_receive_string(self, communicate):
        self.send_communicate(communicate)
        return self.receive_string()