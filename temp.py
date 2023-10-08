from bson import ObjectId

from pymongo import MongoClient


# from src.core.config import settings

DATABASE_URL="mongodb://root:example@localhost:27017/?authSource=admin"

db = MongoClient(DATABASE_URL)['university']

user = {
    "username": "Vitaly",
    "age": 22
}

# response = db["practice_one.variants"].aggregate([{ '$sample': { 'size': 1 } }])
# variant = [variant for variant in response][0]
response = db["test"].update_one({"name": "test2"}, {"$set": {"name": "test3"}})
print(f"response is {response.modified_count}")
# print(f"variant is {variant['_id']}")

# group = db['groups'].find_one({"name": group_name})

# print(f"data is {data}")