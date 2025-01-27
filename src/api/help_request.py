from fastapi import APIRouter, status, Depends, HTTPException

from db.state import WebsocketServiceState

router = APIRouter(tags=['help request'], prefix='/help-request')

@router.post(
    '/{computer_id}',
    status_code=status.HTTP_200_OK
)
async def create_help_request(computer_id: int):
    WebsocketServiceState.connected_computers[computer_id].help_requested = True

@router.post(
    '/{computer_id}/cancel',
    status_code=status.HTTP_200_OK
)
async def create_help_request(computer_id: int):
    WebsocketServiceState.connected_computers[computer_id].help_requested = False
