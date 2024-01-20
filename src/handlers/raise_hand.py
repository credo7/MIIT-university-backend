from pymongo.database import Database
from bson import ObjectId

from db.mongo import CollectionNames
from db.state import State
from schemas import UserOut
from services.connection_manager import ConnectionManager
from services.utils import normalize_mongo


class RaiseHand:
    def __init__(self, state: State, db: Database):
        self.state = state
        self.manager = state.manager
        self.db = db

    async def run(self, computer_id: int, *_args, **_kwargs):
        connected_computers = await self.state.get_connected_computers()
        computer = connected_computers[computer_id]
        users_ids = [ObjectId(id) for id in computer.users_ids]

        users_db = self.db[CollectionNames.USERS.value].find({'id': {'$in': users_ids}})

        users = await normalize_mongo(users_db, UserOut, return_dict=True)

        payload = {'computer_id': computer_id, 'users': users}

        await self.manager.broadcast({'type': 'RAISE_HAND', 'payload': payload})
