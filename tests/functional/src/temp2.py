import socketio


sio = socketio.Client()


@sio.event
def connected_computers(data):
    print(f"connected computers are {data}")


@sio.event
def events_status(data):
    print(f"events_status is {events_status}")


@sio.event
def logs(data):
    print(f"logs are {data}")


@sio.event
def errors(data):
    print(f"errors are {data}")


def main():
    # Connect to the Socket.IO server
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwiZXhwIjoxNjkyNTU5MDk0fQ.m_oCpS2UIMUbI-bwMQjVE9IUZ6CFXVQBaYlJbzCgd00'
    headers = {'Authorization': f'Bearer {token}', 'computer_id': '1'}
    sio.connect('http://localhost:3002', headers=headers)

    sio.wait()


if __name__ == "__main__":
    main()