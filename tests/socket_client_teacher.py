import requests

from custom_socket import CustomSocketIO

api_url = 'http://95.163.236.35:3001'
socket_url = 'http://95.163.236.35:3002'


def login(username: str, password: str):
    response = requests.post(
        f'{api_url}/auth/login', data={'username': username, 'password': password}
    )
    return response.json().get('access_token') if response.content else None


# student_token = login(username="peniigfirst", password="password")
teacher_token = login(username='trniigfirst', password='password')

print('Teacher token: {}'.format(teacher_token))
# print("Student token: {}".format(student_token))


def custom_headers(token: str, computer_id: int) -> dict:
    return {'Authorization': f'Bearer {token}', 'computer_id': str(computer_id)}


fake_events = [
    {'id': 1, 'type': 1, 'mode': 'CLASS'},
]


socket_url = 'http://localhost:3002'
# student_sio = CustomSocketIO(socket_url=socket_url, headers=custom_headers(token=student_token, computer_id=1), computer_id=1)
teacher_sio = CustomSocketIO(
    socket_url=socket_url, headers=custom_headers(token=teacher_token, computer_id=2)
)

# student_sio.start()
teacher_sio.start()

# teacher_sio.send_events(fake_events)
