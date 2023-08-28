from typing import Optional
import redis

import socketio


class CustomSocketIOClient:
    def __init__(
        self,
        api_url: str,
        socket_url: str,
        user_token: str,
        user_token2: Optional[str],
        computer_id: int,
        client_name: str,
    ):
        self.api_url = api_url
        self.socket_url = socket_url
        self.sio = socketio.Client()
        self.client_name = client_name
        self.computer_id = computer_id
        self.user_token = user_token
        self.user_token2 = user_token2
        self.headers = self._get_custom_headers()

        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)

    def connect_and_listen(self):
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.rpush('logs', '228')
        try:
            r.rpush('logs', f'in_connect_and_listen. socket_url={self.socket_url}, headers={self.headers}')
            self.sio.connect(self.socket_url, headers=self.headers)
            r.rpush('logs', f'after self.sio.connect, before self.sio.wait')
            self.sio.wait()
            r.rpush('logs', f'after self.sio.wait')
        except Exception as e:
            r.rpush('errors', str(e))

    def connect(self):
        self.sio.connect(self.socket_url, headers=self.headers)
        # self.sio.wait()

    def disconnect(self):
        self.sio.disconnect()

    def _on_connect(self):
        print(f'{self.client_name} connected to server')

    def _on_disconnect(self):
        print(f'{self.client_name} disconnected from server')

    def _get_custom_headers(self) -> dict:
        headers = {'Authorization': f'Bearer {self.user_token}', 'computer_id': str(self.computer_id)}

        if self.user_token2:
            headers['Authorization_two'] = f'Bearer {self.user_token2}'

        return headers
