from fastapi import APIRouter, status

from db.state import WebsocketServiceState
from schemas import ConnectedComputerUpdate

router = APIRouter(tags=['computer state'], prefix='/computer-state')


@router.post(
    '/update-action-time/{computer_id}',
    status_code=status.HTTP_200_OK
)
async def update_action_time(computer_id: int):
    update_computer = ConnectedComputerUpdate(id=computer_id)
    await WebsocketServiceState.update_connected_computer(update_computer)

@router.delete(
    '/{computer_id}',
    status_code=status.HTTP_200_OK
)
async def remove_computer(computer_id: int):
    if computer_id in WebsocketServiceState.connected_computers:
        del WebsocketServiceState.connected_computers[computer_id]
