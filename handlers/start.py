from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from ..keyboards import main_menu, default_menu


def get_router(db_handler: 'Handler', author_link: str) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message):
        db_handler.add_user(message.from_user.username)
        await message.answer(
            "Привет! Я - Рокси, твой помощник для доступа к прокси-серверу PyROXY.\n\n"
            "Через меня ты можешь получить учётные данные для подключения к прокси и управлять доступом.\n\n"
            "[🔗 Гитхаб разработчика](https://github.com/Pos1t1veGuy)\n"
            f"[🔗 Контакт с разработчиком]({author_link})",
            parse_mode="Markdown", reply_markup=main_menu
        )

    @router.callback_query(F.data.startswith("cancel"))
    async def cancel(callback, state):
        try:
            args = callback.data.split(":")
            if args[-1] == 'delete' and len(args) > 1:
                await callback.message.delete()
            else:
                await callback.message.edit_text(
                    text="❌ Операция отменена",
                    reply_markup=default_menu
                )

        except (TelegramBadRequest, TelegramAPIError):
            pass

    return router