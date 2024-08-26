import logging
import threading

import telebot

from core.config import settings


class TelegramLoggerHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.bot = telebot.TeleBot(settings.telegram_bot_token)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            text = f'{record.levelname}: {record.message}\n'
            if record.exc_info:
                text += f'\n{str(record.exc_text).replace("<", "(").replace(">", ")")}'

            print(f'text={text}')

            if 'bcrypt' in text:
                return

            from call_function_with_timeout import SetTimeout

            class BackgroundTask(threading.Thread):
                def __init__(self, bot):
                    super().__init__()
                    self.bot = bot

                def run(self, *args, **kwargs):
                    func_with_timeout = SetTimeout(self.bot.send_message, timeout=1)
                    _is_done, _is_timeout, _erro_message, _results = func_with_timeout(
                        chat_id=settings.telegram_chat_id, text=text
                    )

            t = BackgroundTask(self.bot)
            t.start()

        except Exception as exc:
            pass


def tg_wrapper(logger: logging.Logger):
    tg_handler = TelegramLoggerHandler()
    logger.addHandler(tg_handler)
