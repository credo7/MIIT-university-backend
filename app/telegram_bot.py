import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import settings


class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token, parse_mode=types.ParseMode.HTML)
        self.storage = MemoryStorage()
        self.dispatcher = Dispatcher(self.bot, self.storage)
        self.chat_id = settings.telegram_chat_id

    async def send_message(self, text):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text)
        except Exception as e:
            logging.error(f"Error sending message to {self.chat_id}: {e}")

    def send_message_async(self, text):
        asyncio.run(self.send_message(text))
