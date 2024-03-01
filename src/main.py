import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import auth, group, user, event, ws
from core.config import settings
from db.mongo import get_db, CollectionNames
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
# app.include_router(lesson.router)
app.include_router(ws.router)


app.add_middleware(ErrorLogHandlingMiddleware)


import uvicorn

def make_me_teacher():
    db = get_db()
    from bson import ObjectId
    inserted = db[CollectionNames.USERS.value].update_one({"_id": ObjectId("65e205c9fa31762cd37c9cd3")}, {
        "$set": {
            "approved": True
        }
    })
        # "_id": ObjectId("65e205c9fa31762cd37c9cd3")}, {
        # {"$set": {"approved": True}
        #  })

    print(inserted)

if __name__ == '__main__':
    make_me_teacher()
    uvicorn.run(app, host='0.0.0.0', port=settings.api_port)
