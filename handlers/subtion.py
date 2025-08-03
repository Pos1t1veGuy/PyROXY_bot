from aiogram import Router, F
from keyboards import balance_menu


def get_router() -> Router:
    router = Router()

    @router.callback_query(F.data == "subscription")
    async def cmd_subtion(callback):
        await callback.message.answer(f"Ваш текущий баланс: {0}", reply_markup=balance_menu)
        await callback.answer()

    return router