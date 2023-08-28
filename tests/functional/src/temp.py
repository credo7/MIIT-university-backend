import socketio
import redis
from multiprocessing import Process
import time

sio = socketio.Client()

redis_client = redis.Redis(host='localhost', port=6379, db=0)


# def listen_to_redis_queue():
#     while True:
#         message = redis_client.lpop('send_logs')
#         if message:
#             # Emit the message to the 'logs' event on the Socket.IO server
#             sio.emit('logs', message.decode('utf-8'))  # Convert bytes to string


def main():
    # Connect to the Socket.IO server
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyNDAsImV4cCI6MTY5MjU2NjI1OH0.D3b_SWdDcc5rz6z0PzQAX_upy80PzDh6nU3CWWgsmtQ'
    headers = {'Authorization': f'Bearer {token}', 'computer_id': '5'}
    sio.connect('http://localhost:3002', headers=headers)

    # Create and start the process to listen to the Redis queue
    # redis_process = Process(target=listen_to_redis_queue)
    # redis_process.start()

    # try:
    #     # Listen to events in the foreground
    sio.call('logs', 'checking')
    while True:
        message = redis_client.lpop('send_logs')
        if message:
            # Emit the message to the 'logs' event on the Socket.IO server
            sio.emit('logs', message)  # Convert bytes to string
    #
    #     sio.wait()
    # finally:
    #     # Clean up and close the Socket.IO connection when the script exits
    #     sio.disconnect()
    #     redis_process.terminate()  # Terminate the Redis process


if __name__ == "__main__":
    main()
