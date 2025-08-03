from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

config = json.load(open("config.json"))
bot_url = config["bot_url"]
ciphers = config["ciphers"]

default_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="На главную", url=f"{bot_url}?start=main")],
])
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌐 О VPN", callback_data="about")],
    [InlineKeyboardButton(text="🔑 Подключить VPN", callback_data="connect")],
    [InlineKeyboardButton(text="💳 Подписка", callback_data="subscription")],
])

cipher_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=cipher, callback_data=f"cipher:{cipher}")] for cipher in ciphers
])

select_user_key = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔁 Использовать предыдущий ключ", callback_data="use_last_key")],
    [InlineKeyboardButton(text="🎲 Сгенерировать случайный ключ", callback_data="generate_new_key")],
    [InlineKeyboardButton(text="❌ Отмена", url=f"{bot_url}?start=main")],
])

balance_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Пополнить", callback_data="top_up")],
    [InlineKeyboardButton(text="Тарифы", callback_data="subscriptions")],
    [InlineKeyboardButton(text="На главную", url=f"{bot_url}?start=main")],
])
