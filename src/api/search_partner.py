import logging

from fastapi import APIRouter, Depends, HTTPException, status
from db.state import State
from schemas import SearchPartner, InvitePartner, AcceptInvite, RejectInvite
from services.oauth2 import extract_users_ids_rest
from services.ws import broadcast_connected_computers

router = APIRouter(tags=['Lessons'], prefix='')

logger = logging.getLogger(__name__)


@router.post('/search-partner', status_code=status.HTTP_200_OK)
async def search_partner(search_partner_dto: SearchPartner, users_ids: list[str] = Depends(extract_users_ids_rest)):
    if len(users_ids) > 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вас уже двое')

    if search_partner_dto.computer_id not in State.connected_computers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вы не подключены к WS')

    State.connected_computers[search_partner_dto.computer_id].is_searching_someone = True

    await broadcast_connected_computers()


@router.post('/stop-search-partner', status_code=status.HTTP_200_OK)
async def stop_search_partner(search_partner_dto: SearchPartner,):
    if search_partner_dto.computer_id not in State.connected_computers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Вы не подключены к WS')

    State.connected_computers[search_partner_dto.computer_id].is_searching_someone = False

    await broadcast_connected_computers()


@router.post('/invite-partner', status_code=status.HTTP_200_OK)
async def invite_someone(invite_partner_dto: InvitePartner):
    if invite_partner_dto.computer_id not in State.connected_computers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Юзер не подключен к WS')

    if not State.connected_computers[invite_partner_dto.computer_id].is_searching_someone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Юзер не ищет пару, либо уже нашел её')

    response = {
        'type': 'INVITE_STUDENT_REQUEST',
        'payload': {
            'requester_computer_id': invite_partner_dto.computer_id,
            'receiver_computer_id': invite_partner_dto.partner_computer_id,
        },
    }

    State.manager.broadcast(response)


@router.post('accept-invite', status_code=status.HTTP_200_OK)
async def accept_invite(accept_invite_dto: AcceptInvite):
    if accept_invite_dto.partner_computer_id not in State.connected_computers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Партнер не подключен к WS')

    if not State.connected_computers[accept_invite_dto.partner_computer_id].is_searching_someone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Партнер не ищет пару, либо уже нашел её')

    response = {
        'type': 'INVITE_REQUEST_ACCEPTED',
        'payload': {
            'requester_computer_id': accept_invite_dto.partner_computer_id,
            'receiver_computer_id': accept_invite_dto.computer_id,
        },
    }

    State.manager.broadcast(response)

    State.connected_computers[accept_invite_dto.partner_computer_id].is_searching_someone = False

    del State.connected_computers[accept_invite_dto.computer_id]

    await broadcast_connected_computers()


@router.post('reject-invite', status_code=status.HTTP_200_OK)
async def cancel_invite(reject_invite_dto: RejectInvite):
    response = {
        'type': 'INVITE_REQUEST_REJECTED',
        'payload': {
            'requester_computer_id': reject_invite_dto.partner_computer_id,
            'receiver_computer_id': reject_invite_dto.computer_id,
        },
    }

    State.manager.broadcast(response)
