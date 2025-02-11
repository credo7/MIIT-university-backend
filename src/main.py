import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, group, user, event, help_request, ws, dev, computer_state
from services.error_log_handling_middleware import ErrorLogHandlingMiddleware
from tg_logger import tg_wrapper

logging.basicConfig(level=logging.INFO, filename='../app.log', format='%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
logger = logging.getLogger("")
logger.addHandler(console_handler)
tg_wrapper(logger)


app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'],
)


app.include_router(auth.router)
app.include_router(group.router)
app.include_router(user.router)
app.include_router(event.router)
app.include_router(help_request.router)
app.include_router(dev.router)
app.include_router(ws.router)
app.include_router(computer_state.router)


app.add_middleware(ErrorLogHandlingMiddleware)


import uvicorn

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)  # settings.api_port)
