import asyncio
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import Message, CallbackQuery

from ..keyboards import default_menu


async def msg_timeout(state, sent, bot, timeout=60*5):
    await state.update_data(
        timeout_msg=[sent.message_id, sent.chat.id]
    )

    await asyncio.sleep(timeout)

    data = await state.get_data()
    msg = data.get("timeout_msg")

    if msg != -1:
        try:
            await sent.edit_text(
                text="⏳ Время на выбор истекло. Попробуйте ещё раз.",
                reply_markup=default_menu
            )
        except (TelegramBadRequest, TelegramAPIError):
            pass

async def disable_msg_timeout(state):
    await state.update_data(
        last_send_time=-1
    )

def format_username(object: Message | CallbackQuery) -> str:
    return f'id_{object.from_user.id}'