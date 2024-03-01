from db.state import State
from schemas import UserOut


def search_partner(computer_id: int):
    State.connected_computers[computer_id].is_searching_someone = True


def invite_someone(
        requester_computer_id: int,
        receiver_computer_id: int,
        requester_user: UserOut
):
    response = {
        "type": "INVITE_STUDENT_REQUEST",
        "payload": {
            "requester_computer_id": requester_computer_id,
            "receiver_computer_id": receiver_computer_id
        }
    }

    State.manager.broadcast(response)


def accept_invite_request(requester_computer_id: int, receiver_computer_id: int):
    return {
        "type": "ACCEPT_INVITE_REQUEST",
        "payload": {
            "requester_computer_id": requester_computer_id,
            "receiver_computer_id": receiver_computer_id
        }
    }
