import json
import asyncio
import re
from aiogram import Bot, Dispatcher, Router, F
from pathlib import Path
from .handlers import start, about, connect, subtion
from .db_handler import SQLite_Handler
from .keyboards import config


DEFAULT_SERVER_KEY = open(Path(__file__).parent / 'default_server_key', 'r').read()
author_link = config['author_link']
author_id = config['author_id']
bot_url = config['bot_url']
clients_url = config['clients_url']
ciphers = config['ciphers']
payment_methods = config['payment_methods']

bot = Bot(token=config["API_TOKEN"])
dp = Dispatcher()

db_handler = SQLite_Handler(Path(__file__).parent / 'db.sqlite3')
main_router = Router()
dp.include_router(start.get_router(db_handler, author_link))
dp.include_router(about.get_router(author_link))
dp.include_router(connect.ConnectRouter(db_handler, clients_url, DEFAULT_SERVER_KEY, ciphers).router)
dp.include_router(subtion.SubtionRouter(db_handler, payment_methods, author_id).router)


@main_router.message(F.from_user.id == author_id)
async def admin_message(message):
    if not message.reply_to_message:
        return

    original = message.reply_to_message
    if not original.text or not original.text.startswith("💰 Новый запрос на пополнение!"):
        return

    try:
        amount = int(message.text.strip())
    except ValueError:
        return

    m_user = re.search(r"ID:\s*(\d+)", original.text)
    m_payment = re.search(r">\s*(\d+)", original.text)

    if not m_user or not m_payment:
        await message.reply("❌ Ошибка парсинга данных из сообщения")

    user_id = int(m_user.group(1))
    payment_id = int(m_payment.group(1))

    if amount > 0:
        if await db_handler.confirm_payment(payment_id, amount):
            await message.reply(f"✅ Пользователю {user_id} зачислено {amount} руб.")
            text = "✅ Ваш платёж успешно зачислен!"
        else:
            await message.reply(f"❌ Невозможно начислить деньги пользователю {user_id}")
            text = "❌ Ваш платёж отклонен!"

    else:
        await db_handler.reject_payment(payment_id)
        await message.reply(f"❌ Пользователю {user_id} отказано в пополнении")
        text = "❌ Ваш платёж отклонен!"

    await bot.send_message(user_id, text)
    await original.delete()

async def main():
    await db_handler.connect()
    await dp.start_polling(bot)
    await db_handler.close()


dp.include_router(main_router)


if __name__ == "__main__":
    asyncio.run(main())