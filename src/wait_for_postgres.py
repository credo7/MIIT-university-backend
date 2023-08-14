import time

import psycopg2
from psycopg2 import OperationalError
from core.config import settings


def wait_for_postgres(db_url: str, retry_interval: int = 5, max_retries: int = 100):
    retries = 0
    while True:
        try:
            connection = psycopg2.connect(db_url)
            print('Connection successful! PostgreSQL is loaded.')
            connection.close()
            return
        except OperationalError:
            print(f'Connection attempt {retries + 1}/{max_retries} failed. Retrying in {retry_interval} seconds...')
            retries += 1
            time.sleep(retry_interval)


if __name__ == '__main__':
    wait_for_postgres(settings.database_url)
