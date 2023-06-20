import multiprocessing as mp

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from routers import auth, user, group
from socket_server import start_socket_server
from logger_middleware import custom_logger_middleware
from config import settings

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(group.router)
app.include_router(user.router)

# app.middleware('http')(custom_logger_middleware)


@app.get("/")
async def root():
    return {"message": "Reloaded"}


def start_fastapi_server():
    uvicorn.run(app, host='0.0.0.0', port=settings.fastapi_port)


if __name__ == "__main__":
    # start_socket_server()
    socket_process = mp.Process(target=start_socket_server)
    socket_process.start()

    fastapi_process = mp.Process(target=start_fastapi_server)
    fastapi_process.start()

    socket_process.join()
    fastapi_process.join()
