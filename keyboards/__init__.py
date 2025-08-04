from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

config = json.load(open("config.json", 'r', encoding='utf-8'))
bot_url = config["bot_url"]
ciphers = config["ciphers"]
payment_methods = config["payment_methods"]
pricing = config["pricing"]
money_to_pay = config["money_to_pay"]


default_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏠 На главную", url=f"{bot_url}?start=main")],
])
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌐 О VPN", callback_data="about")],
    [InlineKeyboardButton(text="🔑 Подключить VPN", callback_data="connect")],
    [InlineKeyboardButton(text="💳 Подписка", callback_data="subscription")],
    [InlineKeyboardButton(text="❓ Как подключиться", callback_data="connect_guide")],
])

cipher_buttons_menu = InlineKeyboardMarkup(inline_keyboard=[
    *[[InlineKeyboardButton(text=f'🔒 {cipher}', callback_data=f"cipher:{cipher}")] for cipher in ciphers],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])
how_to_connect_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🏠 На главную", url=f"{bot_url}?start=main")],
    [InlineKeyboardButton(text="❓ Подключиться", callback_data="connect_guide")],
])

select_user_key_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔁 Использовать предыдущий ключ", callback_data="use_last_key")],
    [InlineKeyboardButton(text="🎲 Сгенерировать случайный ключ", callback_data="generate_new_key")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])

balance_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Пополнить", callback_data="top_up")],
    [InlineKeyboardButton(text="Тарифы", callback_data="pricing")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])

payment_methods_menu = InlineKeyboardMarkup(inline_keyboard=[
    *[[InlineKeyboardButton(text=f'{method}', callback_data=f"method:{method}")] for method in payment_methods],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])
confirm_payment_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="payment")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])
money_to_pay_menu = InlineKeyboardMarkup(inline_keyboard=[
    *[[InlineKeyboardButton(text=f'{money} рублей', callback_data=f"confirm_payment:{money}")] for money in money_to_pay],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])

pricing_menu = InlineKeyboardMarkup(inline_keyboard=[
    *[
        [InlineKeyboardButton(
            text=f'{price["comment"]} 📅 {price["price"]}р.',
            callback_data=f"confirm_buy:{name}:{price['price']}:{price['once']}"
        )]
        for name, price in pricing.items()
    ],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])
confirm_buy_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Купить", callback_data="buy")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
])