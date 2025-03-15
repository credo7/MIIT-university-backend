import json, time
from typing import List

from pymongo import MongoClient
from pymongo.database import Database

from core.config import settings
from db.mongo import CollectionNames

files_to_init_map = {
    # 'practice_one': 'practice_one_info.json',
    # "practice_one.steps": "practice_one_steps.json",
    # "practice_one.variants": "practice_one_variants.json",
    # "practice_two.containers": "practice_two_containers.json",
    # "practice_two.points": "practice_two_points.json",
    # "practice_two.risks": "practice_two_risks.json",
    # "practice_two.routes": "practice_two_routes.json",
    # "practice_two.steps": "practice_two_steps.json",
    # "practice_two.variants": "practice_two_variants.json",
}


def get_database(retry_interval: int = 5, max_retries: int = 100) -> Database:
    retries = 0
    while True:
        try:
            database = MongoClient(settings.database_url)['university']
            database.command('ping')
            return database
        except Exception:
            print(f'Connection attempt {retries + 1}/{max_retries} failed. Retrying in {retry_interval} seconds...')
            retries += 1
            time.sleep(retry_interval)


if __name__ == '__main__':
    db = get_database()

    # exist_collections = db.list_collection_names()
    #
    # for collection, file_path in files_to_init_map.items():
    #     if collection in exist_collections:
    #         continue
    #     with open(f"../data_files/{file_path}", 'r') as file:
    #         data = json.load(file)
    #         if isinstance(data, List):
    #             db[collection].insert_many(data)
    #         else:
    #             db[collection].insert_one(data)
