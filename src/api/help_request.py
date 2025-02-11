from fastapi import APIRouter, status, Depends, HTTPException

from db.state import WebsocketServiceState
from schemas import ConnectedComputerUpdate

router = APIRouter(tags=['help request'], prefix='/help-request')

@router.post(
    '/{computer_id}',
    status_code=status.HTTP_200_OK
)
async def create_help_request(computer_id: int):
    update_computer = ConnectedComputerUpdate(id=computer_id, help_requested=True)
    await WebsocketServiceState.update_connected_computer(update_computer)

@router.post(
    '/{computer_id}/cancel',
    status_code=status.HTTP_200_OK
)
async def stop_help_request(computer_id: int):
    update_computer = ConnectedComputerUpdate(id=computer_id, help_requested=False)
    await WebsocketServiceState.update_connected_computer(update_computer)
