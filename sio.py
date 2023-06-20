from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")


@socketio.on('message')
def handle_event(message):
    print('Received message:', message)
    emit('response', {'data': 'Message received'})


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


def application(_, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield b'Hello, World!\n'


if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5000)
