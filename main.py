import json
import asyncio
from aiogram import Bot, Dispatcher
from handlers import start, about, connect, subtion
from db_handler import is_subscriber, save_key, find_key

CONFIG_FILE = 'config.json'
CMD_STRING = '--host={host} --username={username} --password={password} --key={key} --cipher={cipher}'

config = json.load(open(CONFIG_FILE, 'r')) # API_TOKEN, author_link keys required
author_link = config['author_link']
bot_url = config['bot_url']
ciphers = config['ciphers']

bot = Bot(token=config["API_TOKEN"])
dp = Dispatcher()

dp.include_router(start.get_router())
dp.include_router(about.get_router(author_link))
dp.include_router(connect.ConnectRouter(is_subscriber, save_key, find_key).router)
dp.include_router(subtion.get_router())

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))