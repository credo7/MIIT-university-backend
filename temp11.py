from src.db.mongo import get_db
from bson import ObjectId

db = get_db()
db['users'].update_one({'_id': ObjectId('65e2ffc03613d3354300781f')}, {'$set': {'approved': True}})
