from aiogram import Router, F
from keyboards import default_menu

router = Router()

def get_router(author_link: str) -> Router:
    router = Router()

    @router.callback_query(F.data == "about")
    async def cmd_about(callback):
        await callback.message.answer(
            "⚙️ <b>О проекте PyROXY</b>\n\n"
            "🔒 <b>PyROXY</b> — это быстрый, надёжный и защищённый VPN, основанный на модифицированном протоколе SOCKS5 "
            "с добавлением <b>кастомного шифрования</b>.\n\n"
            "💻 Чтобы начать пользоваться, необходимо установить прокси-клиент автора на свой ПК. "
            "Он прост в использовании и подходит для повседневного безопасного серфинга в интернете.\n\n"
            "🚀 <b>Преимущества:</b>\n"
            "• Высокая скорость соединения\n"
            "• Пользовательское шифрование для обхода блокировок\n"
            "• Незаметность трафика для провайдеров и наблюдателей\n\n"
            "🆓 <b>Для новых пользователей</b> предоставляется <u>бесплатный 3-дневный период</u>.\n"
            "Далее необходимо приобрести подписку, чтобы продолжить пользоваться сервисом.\n\n"
            f"📩 <b>Есть вопросы?</b> Свяжитесь с автором: {author_link}",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=default_menu
        )
        await callback.answer()

    return router