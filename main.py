import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio


CONFIG_FILE = 'config.json'
config = json.load(open(CONFIG_FILE, 'r')) # API_TOKEN, author_link keys required
author_link = config['author_link']

bot = Bot(token=config['API_TOKEN'])
dp = Dispatcher()
router = Router()
dp.include_router(router)


main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌐 О VPN", callback_data="about")],
    [InlineKeyboardButton(text="🔑 Подключить VPN", callback_data="connect")],
    [InlineKeyboardButton(text="💳 Подписка", callback_data="subscription")],
])


@router.message(Command("start"))
async def cmd_start(message):
    await message.answer(
        "Привет! Я - Рокси, твой помощник для доступа к прокси-серверу PyROXY.\n\n"
        "Через меня ты можешь получить учётные данные для подключения к прокси и управлять доступом.\n"
        "Также через меня ты можешь связаться напрямую с моим создателем для вопросов и поддержки.\n\n"
        "🔗 Мой создатель: [Pos1t1veGuy](https://github.com/Pos1t1veGuy)\n\n",
        parse_mode="Markdown", reply_markup=main_menu, disable_web_page_preview=True,
    )

@router.callback_query(F.data == "about")
async def cmd_about(callback):
    await callback.message.answer(
        "⚙️ <b>О PyROXY:</b>\n"
        "PyROXY - это быстрый и надежный VPN, написанный на модификации протокола SOCKS5 с добавлением пользовательского"
        "шифрования. Чтобы начать пользоваться этим VPN, нужно установить прокси-клиент моего автора на свой ПК."
        "Плюсы этого VPN - супер защищенность и скорость. Защита, в том числе пользовательские настройки шифрования,"
        "позволяет обходить блокировки и делать трафик нечитабельным для посторонних.\n\n"
        "Если вас заинтересовал данный проект, то для новых пользователей есть бесплатный трехдневный период, но затем "
        "необходимо преобрести подписку."
        f"Если у вас есть вопросы, вы можете связаться с автором: {author_link}",
        parse_mode="HTML"
    )
    await callback.answer()

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))