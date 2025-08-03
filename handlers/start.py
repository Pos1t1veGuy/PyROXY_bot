from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboards import main_menu

def get_router() -> Router:
    router = Router()
    @router.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer(
            "Привет! Я - Рокси, твой помощник для доступа к прокси-серверу PyROXY.\n\n"
            "Через меня ты можешь получить учётные данные для подключения к прокси и управлять доступом.\n\n"
            "🔗 Мой создатель: [Pos1t1veGuy](https://github.com/Pos1t1veGuy)",
            parse_mode="Markdown", reply_markup=main_menu
        )
    return router