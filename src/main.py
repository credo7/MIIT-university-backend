import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import auth, group, user, event, ws

logger = logging.getLogger(__name__)

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'],
)


app.include_router(auth.router)
app.include_router(group.router)
app.include_router(user.router)
app.include_router(event.router)
app.include_router(ws.router)


@app.middleware("http")
async def modify_request_response_middleware(request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Error in path: {request.url.path}, Traceback: {exc}", exc_info=True)
        response = JSONResponse(content={
            "error": str(exc),
            "hint": "Снова этот @swagv напортачил?..",
            "hint2": "Не переживай, исправим"
        }, status_code=500)
    return response


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001)
