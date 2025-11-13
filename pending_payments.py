from typing import *
import sqlite3
import logging
import asyncio
import json
from pathlib import Path
from aiogram import Bot

from .db_handler import Handler, SQLite_Handler, PostgresHandler


CONFIG_FILE = 'config.json'
config = json.load(open(Path(__file__).parent / CONFIG_FILE, 'r', encoding='utf-8'))
bot = Bot(token=config["API_TOKEN"])
logging.basicConfig(
    filename="payments.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)


async def process_pending_payments(db: Handler, do_after: Callable[[str, int, str, bool, int], None]):
    payments = await db.list_pending_payments()

    if not payments:
        logger.info("Нет ожидающих оплат.")
        return

    for payment in payments:
        payment_id, username, details, user_id, requested_at = payment

        logger.info("\n=================\n"
                    f"ID: {payment_id}\n"
                    f"Username: {username}\n"
                    f"User ID: {user_id}\n"
                    f"Детали: {details}\n"
                    f"Запрошен: {requested_at}\n")

        try:
            choice = float(input("Сколько денег начислено?: ").strip().lower())
            if choice <= 0:
                await db.reject_payment(payment_id)
                logger.info("Оплата отклонена.")
                await do_after(username, user_id, details, choice > 0, choice)
                continue
            else:
                if await db.confirm_payment(payment_id, choice):
                    logger.info("Оплата подтверждена.")
                    await do_after(username, user_id, details, choice > 0, choice)
                    continue
                else:
                    logger.warning("Невозможно оплатить, вероятно пользователя нет в базе.")
        except ValueError:
            logger.error(f"Некорректный ввод при оплате ID={payment_id}: {choice}")


async def callback(username: str, user_id: int, details: str, accepted: bool, money: int):
    if accepted:
        status = "подтверждена"
        text = "✅ Ваш платёж успешно зачислен!"
    else:
        status = "отклонена"
        text = "❌ Ваш платёж отклонен!"

    try:
        await bot.send_message(user_id, text)
        logger.info(f"Оплата от {username} ({user_id}) с деталями '{details}' {status}. Начислено {money}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")


if __name__ == "__main__":
    db = SQLite_Handler()
    asyncio.run(process_pending_payments(db, callback))