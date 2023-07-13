import socketio


class CustomSocketIO:
    def __init__(self, socket_url, computer_id=None, headers=None):
        self.sio = socketio.Client()
        self.socket_url = socket_url
        self.headers = headers
        self.computer_id = computer_id

        self.received_messages = []

        self.sio.on('connect', self.on_connect)
        self.sio.on('my_message', self.on_my_message)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('user_joined_broadcast', self.user_joined_broadcast)
        self.sio.on('connected_computers', self.connected_computers)
        self.sio.on(f'computer_{self.computer_id}_event', self.computer_event)
        self.sio.on('session_id', self.session_id)
        self.sio.on('events_status', self.events_status)
        self.sio.on(f'computer_{computer_id}_results', self.computer_results)

    def start(self):
        self.sio.connect(self.socket_url, headers=self.headers)

    def on_connect(self):
        print('Connected to server')

    def on_my_message(self, data):
        print('Received message:', data)
        self.received_messages.append(data)

    def on_disconnect(self):
        print('Disconnected from server')

    def send_message(self, message):
        self.sio.emit('my_message', message)

    def user_joined_broadcast(self, message):
        print(message)

    def connected_computers(self, message):
        print('Connected computers are: ', message)

    def send_events(self, events):
        self.sio.emit('start_events', events)

    def computer_event(self, message):
        print(message)

    def session_id(self, message):
        print(message)

    def events_status(self, message):
        print(message)

    def computer_results(self, message):
        print(message)
