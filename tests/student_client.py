from typing import Optional

from .custom_socketio_client import CustomSocketIOClient


class StudentClient(CustomSocketIOClient):
    def __init__(
        self,
        api_url: str,
        socket_url: str,
        user_token: str,
        user_token2: Optional[str],
        computer_id: int,
        client_name: str,
    ):
        super().__init__(api_url, socket_url, user_token, user_token2, computer_id, client_name)

        self.sio.on(f'computer_{self.computer_id}_event', self._on_event)
        self.sio.on(f'computer_{self.computer_id}_results', self._on_event)

    def send_logs(self, message):
        self.sio.emit('logs', message)

    def _on_event(self, data):
        print(f'{self.client_name} | _on_event data is : {data}')

    def _on_results(self, data):
        print(print(f'{self.client_name} | _on_results data is : {data}'))
