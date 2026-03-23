import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, computer_state, dev, event, group, help_request, user, ws
from core.config import settings
from db.mongo import close_mongo_connection, connect_to_mongo
from db.state import WebsocketServiceState
from services.error_log_handling_middleware import ErrorLogHandlingMiddleware

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    filename=settings.log_file,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger("")
logger.addHandler(console_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    asyncio.create_task(WebsocketServiceState.clean_expired_computers())
    logger.info("Приложение запущено")
    yield
    await close_mongo_connection()
    logger.info("Приложение остановлено")


app = FastAPI(lifespan=lifespan)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(ErrorLogHandlingMiddleware)

app.include_router(auth.router)
app.include_router(group.router)
app.include_router(user.router)
app.include_router(event.router)
app.include_router(help_request.router)
app.include_router(dev.router)
app.include_router(ws.router)
app.include_router(computer_state.router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=settings.api_port)
