from typing import Callable, Awaitable
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse

from services.oauth2 import extract_users_ids

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class ErrorLogHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger = logging.getLogger(__name__)
        users_ids = None
        try:
            users_ids = await extract_users_ids(request.headers)
            response = await call_next(request)
        except HTTPException as exc:
            logger.error(f'Error in path: {request.url.path}, users_ids={users_ids} Traceback: {exc}', exc_info=True)
            response = JSONResponse(content={'error': exc.detail}, status_code=exc.status_code)
        except Exception as exc:
            logger.error(f'Error in path: {request.url.path}, users_ids={users_ids} Traceback: {exc}', exc_info=True)
            response = JSONResponse(content={'error': str(exc)}, status_code=500)
        return response
