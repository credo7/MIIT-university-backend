from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, group, user, event, ws
from socket_server import SocketServer
from db.postgres import session as db_session

api_app = FastAPI()

origins = ['*']

api_app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'],
)

api_app.include_router(auth.router)
api_app.include_router(group.router)
api_app.include_router(user.router)
api_app.include_router(event.router)
api_app.include_router(ws.router)
# api_app = ws.get_app(api_app)

# @api_app.get('/')
# async def root():
#     return {'message': 'Reloaded'}


socket_app = SocketServer(logger=True, db_session=db_session).app

import uvicorn
if __name__ == "__main__":
    uvicorn.run(api_app, host="0.0.0.0", port=3001)
