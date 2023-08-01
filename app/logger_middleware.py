from time import time

import database
import models
import oauth2
from database import get_db
from fastapi import Request, Response
from sqlalchemy.orm import Session
from telegram_bot import TelegramBot


class CustomLogger:
    def __init__(self, tg: bool):
        self.tg = tg
        self.db = get_db()

    async def log(
        self,
        user_id=None,
        endpoint=None,
        status_code=None,
        request_method=None,
        process_time=None,
        computer_id=None,
        db: Session = database.session,
    ):
        user = None
        if user_id:
            user = db.query(models.User).filter(models.User.id == user_id).first()
        new_log = models.Log(
            user_id=getattr(user, 'id', None),
            endpoint=endpoint,
            computer_id=computer_id,
            status_code=status_code,
            process_time=process_time,
        )

        db.add(new_log)
        db.commit()

        if self.tg:
            tg_bot = TelegramBot()
            username = user.username if user else 'Not defined'
            user_id = user.id if user else 'Not defined'
            request_line = (
                f'{request_method} {endpoint} {status_code}'
                if status_code and request_method and endpoint
                else 'Not defined'
            )

            computer_id = computer_id if computer_id else 'Not defined'
            process_time = process_time if process_time else 'Not defined'

            message = (
                f'🚀 {request_line}\n\n👤 '
                f'User {username} (ID: {user_id})\n\n'
                f'💻 computer_id: {computer_id}\n\n'
                f'⏰ Process time is {process_time}'
            )

            await tg_bot.send_message(message)


async def custom_logger_middleware(request: Request, call_next):
    start_time = time()
    response: Response = await call_next(request)
    process_time = round(time() - start_time, 5)
    auth_header = request.headers.get('Authorization')
    token, computer_id = None, None
    if auth_header and auth_header.startswith('Bearer '):
        bearer_token = auth_header.split('Bearer ')[1]
        token = oauth2.verify_access_token(bearer_token, credentials_exception=None, raise_on_error=False)
    computer_id = request.headers.get('X-Computer-ID')
    await CustomLogger(tg=True).log(
        user_id=token.id if token else None,
        status_code=response.status_code,
        endpoint=request.url.path,
        request_method=request.method,
        process_time=process_time,
        computer_id=computer_id if computer_id else None,
    )
    return response
