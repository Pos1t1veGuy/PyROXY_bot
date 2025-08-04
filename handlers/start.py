from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from keyboards import main_menu, default_menu
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError


def get_router() -> Router:
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message):
        await message.answer(
            "Привет! Я - Рокси, твой помощник для доступа к прокси-серверу PyROXY.\n\n"
            "Через меня ты можешь получить учётные данные для подключения к прокси и управлять доступом.\n\n"
            "🔗 Мой создатель: [Pos1t1veGuy](https://github.com/Pos1t1veGuy)",
            parse_mode="Markdown", reply_markup=main_menu
        )

    @router.callback_query(F.data == 'cancel')
    async def cancel(callback, state):
        try:
            await callback.message.edit_text(
                text="❌ Операция отменена",
                reply_markup=default_menu
            )
        except (TelegramBadRequest, TelegramAPIError):
            pass

    return router