from typing import Dict

from db.state import State
from schemas import ActualizeComputerPayload, ConnectedComputerEdit
from services.ws import broadcast_connected_computers


async def actualize_computer_state(computer_id: int, payload: Dict, *args, **kwargs):
    payload = ActualizeComputerPayload(**payload)
    connected_computer_edit = ConnectedComputerEdit(
        id=computer_id, event_type=payload.event_type, event_mode=payload.event_mode
    )
    State.edit_connected_computer(connected_computer_edit)
    await broadcast_connected_computers()
