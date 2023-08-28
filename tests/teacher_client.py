from .custom_socketio_client import CustomSocketIOClient


class TeacherClient(CustomSocketIOClient):
    def __init__(
        self,
        api_url: str,
        socket_url: str,
        user_token: str,
        computer_id: int,
        client_name: str,
        # logs_enabled: bool = True
    ):
        super().__init__(api_url, socket_url, user_token, None, computer_id, client_name)
        self.sio.on('connected_computers', self._on_connected_computers)
        self.sio.on('events_status', self._on_events_status)

        # if logs_enabled:
        #     self.sio.on('logs', self._on_logs)
        #     self.sio.on('errors', self._on_errors)

    def _on_connected_computers(self, data):
        print(f'{self.client_name} | on_connected_computers data is {data}')

    def _on_events_status(self, data):
        print(f'{self.client_name} | on_connected_computers data is {data}')

    def _on_logs(self, data):
        print(f'{self.client_name} | on_connected_computers data is {data}')

    def _on_errors(self, data):
        print(f'{self.client_name} | on_connected_computers data is {data}')
