from aiogram import Router, F
from keyboards import default_menu

router = Router()

def get_router(author_link: str) -> Router:
    router = Router()

    @router.callback_query(F.data == "about")
    async def cmd_about(callback):
        await callback.message.answer(
            "⚙️ <b>О PyROXY:</b>\n"
            "PyROXY - это быстрый и надежный VPN, написанный на модификации протокола SOCKS5 с добавлением пользовательского"
            "шифрования. Чтобы начать пользоваться этим VPN, нужно установить прокси-клиент моего автора на свой ПК. "
            "Плюсы этого VPN - супер защищенность и скорость. Защита, в том числе пользовательские настройки шифрования,"
            "позволяет обходить блокировки и делать трафик нечитабельным для посторонних.\n\n"
            "Если вас заинтересовал данный проект, то для новых пользователей есть бесплатный трехдневный период, но затем "
            "необходимо преобрести подписку.\n"
            f"Если у вас есть вопросы, вы можете связаться с автором: {author_link}",
            parse_mode="HTML", disable_web_page_preview=True, reply_markup=default_menu
        )
        await callback.answer()

    return router