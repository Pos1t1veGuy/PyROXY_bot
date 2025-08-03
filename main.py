import json
import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, about, connect, subtion
from db_handler import is_subscriber, save_key, save_cipher, save_password, find_key, find_cipher, find_password

CONFIG_FILE = 'config.json'

config = json.load(open(CONFIG_FILE, 'r')) # API_TOKEN, author_link keys required
author_link = config['author_link']
bot_url = config['bot_url']
ciphers = config['ciphers']
host = config['host']

bot = Bot(token=config["API_TOKEN"])
dp = Dispatcher()

dp.include_router(start.get_router())
dp.include_router(about.get_router(author_link))
dp.include_router(connect.ConnectRouter(
    host, is_subscriber, save_key, save_cipher, save_password, find_key, find_cipher, find_password
).router)
dp.include_router(subtion.get_router())

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))