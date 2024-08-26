from pymongo.database import Database
from bson import ObjectId

from db.mongo import CollectionNames
from db.state import WebsocketServiceState
from schemas import UserOut
from services.connection_manager import ConnectionManager
from services.utils import normalize_mongo


class RaiseHand:
    def __init__(self, db: Database):
        self.db = db

    async def run(self, computer_id: int, *_args, **_kwargs):
        pass
        # computer = State.connected_computers[computer_id]
        # users_ids = [ObjectId(id) for id in computer.users_ids]
        #
        # users_db = self.db[CollectionNames.USERS.value].find({'id': {'$in': users_ids}})
        #
        # users = normalize_mongo(users_db, UserOut, return_dict=True)
        #
        # payload = {'computer_id': computer_id, 'users': users}
        #
        # await State.manager.broadcast({'type': 'RAISE_HAND', 'payload': payload})
