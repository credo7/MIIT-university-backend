import multiprocessing as mp

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api import auth, group, user
from socket_server import SocketServer
from db.postgres import session as db_session

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(group.router)
app.include_router(user.router)


@app.get('/')
async def root():
    return {'message': 'Reloaded'}


def start_fastapi_server():
    uvicorn.run(app, host='0.0.0.0', port=settings.fastapi_port)


if __name__ == '__main__':
    socket_server = SocketServer(logger=True, db_session=db_session)

    socket_process = mp.Process(target=socket_server.run)
    socket_process.start()

    fastapi_process = mp.Process(target=start_fastapi_server)
    fastapi_process.start()

    socket_process.join()
    fastapi_process.join()
