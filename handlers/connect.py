from aiogram import Router, F
from keyboards import cipher_buttons, use_last_key

def get_router() -> Router:
    router = Router()

    @router.callback_query(F.data == "connect")
    async def cmd_connect(callback):
        await callback.message.answer("Выберите тип шифрования:", reply_markup=cipher_buttons)
        await callback.answer()

    @router.callback_query(F.data.startswith("cipher:"))
    async def cipher_selected(callback):
        user = callback.from_user
        if subscriber(user.username):
            cipher_type = callback.data.split(":", 1)[1]
            change_cipher(user.username, cipher_type)
            await callback.message.answer(f"Вы выбрали: {cipher_type}")
            await callback.message.answer(
                "А теперь укажите ключ шифрования (просто строка с буквами):", reply_markup=use_last_key
            )
            await callback.answer()

    return router