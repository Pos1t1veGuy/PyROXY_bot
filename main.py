import json
import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, about, connect, subtion
from db_handler import SQLite_Handler

CONFIG_FILE = 'config.json'
DEFAULT_SERVER_KEY = open('default_server_key', 'r').read()

config = json.load(open(CONFIG_FILE, 'r', encoding='utf-8'))
author_link = config['author_link']
author_id = config['author_id']
bot_url = config['bot_url']
host = config['host']
ciphers = config['ciphers']
payment_methods = config['payment_methods']

bot = Bot(token=config["API_TOKEN"])
dp = Dispatcher()

db_handler = SQLite_Handler()
dp.include_router(start.get_router(db_handler))
dp.include_router(about.get_router(author_link))
dp.include_router(connect.ConnectRouter(db_handler, host, DEFAULT_SERVER_KEY, ciphers).router)
dp.include_router(subtion.SubtionRouter(db_handler, payment_methods, author_id).router)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))