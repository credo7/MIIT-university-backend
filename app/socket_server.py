from flask import Flask, request, session
from flask_socketio import SocketIO, disconnect, emit, send

import oauth2
from config import settings
from telegram_bot import TelegramBot

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.flask_secret_key
socketio = SocketIO(app)

tg_bot = TelegramBot()

connected_users = {}


@app.route('/')
def main():
    app.logger.info('Processing request')
    return {"message": "OK"}


@socketio.on('connect')
def handle_connect():
    computer_id = request.args.get('computer_id')
    tg_bot.send_message_async("Computer id is {0}".format(computer_id))
    if not computer_id:
        disconnect()
        tg_bot.send_message_async("Computer id wasn't provided")
        return

    environ = request.environ
    first_token = environ.get('HTTP_AUTHORIZATION')
    second_token = environ.get('HTTP_AUTHORIZATION_TWO')

    if not first_token:
        disconnect()
        tg_bot.send_message_async('AUTHORIZATION header is missing')
        return

    if first_token == second_token:
        disconnect()
        tg_bot.send_message_async('Cannot connect with the same user credentials for both users')
        return

    user = oauth2.get_current_user_socket(first_token)

    if not user:
        disconnect()
        tg_bot.send_message_async('User not found')
        return

    user2 = None
    if second_token:
        user2 = oauth2.get_current_user_socket(second_token)
        if not user2:
            disconnect()
            tg_bot.send_message_async('Second authorization token is not correct')
            return

    connected_users[computer_id] = [user.serialize()]

    if user2:
        connected_users[computer_id].append(user.serialize())

    session["ids"] = [user.id, user2.id if user2 else None]
    session["usernames"] = [user.username, user2.username if user2 else None]
    session["computer_id"] = computer_id

    message = f'User {user.username} with ID {user.id} connected to socket with device id {computer_id}'
    if user2:
        message += f' and {user2.username} with ID {user2.id}'
    else:
        message += ' without a second user'
    tg_bot.send_message_async(message)


@socketio.on('disconnect')
def handle_disconnect():
    if "ids" not in session:
        tg_bot.send_message_async("Client without session was disconnected")
        return

    connected_users.remove(session["computer_id"])

    message = f'User {session["usernames"][0]} with ID {session["ids"][0]} connected to socket'
    if session["ids"][1]:
        message += f' and {session["usernames"][1]} with ID {session["ids"][1]}'
    else:
        message += ' without a second user'

    tg_bot.send_message_async(message)
    print('Client disconnected')


@socketio.on('connected_users')
def handle_connected_users(msg):
    """Emit a list of connected users to the client."""
    tg_bot.send_message_async("In connected users handler, message is {0}".format(msg))
    emit('connected_users_response', {"computers_with_users": connected_users})


def start_socket_server():
    print("Server is starting...")
    socketio.run(app, host='0.0.0.0', port=settings.socket_port)
