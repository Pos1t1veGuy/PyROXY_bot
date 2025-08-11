import json
import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, about, connect, subtion
from db_handler import SQLite_Handler

CONFIG_FILE = 'config.json'
DEFAULT_SERVER_KEY = open('default_server_key', 'r').read()
# сделать кнопки назад и кнопку для настройки пароля
config = json.load(open(CONFIG_FILE, 'r', encoding='utf-8')) # API_TOKEN, author_link keys required
author_link = config['author_link']
bot_url = config['bot_url']
host = config['host']
ciphers = config['ciphers']

bot = Bot(token=config["API_TOKEN"])
dp = Dispatcher()

db_handler = SQLite_Handler()
dp.include_router(start.get_router(db_handler))
dp.include_router(about.get_router(author_link))
dp.include_router(connect.ConnectRouter(host, DEFAULT_SERVER_KEY, ciphers, db_handler).router)
dp.include_router(subtion.SubtionRouter(db_handler).router)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))