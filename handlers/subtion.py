from typing import *
from aiogram import Router, F
from datetime import datetime, timedelta
from keyboards import (balance_menu, default_menu, payment_methods_menu, pricing_menu, money_to_pay_menu,
                       confirm_buy_menu, confirm_payment_menu)
import asyncio

from .utils import msg_timeout, disable_msg_timeout


subtion_router = Router()


class SubtionRouter:
    def __init__(self, db_handler: 'Handler'):

        global subtion_router
        self.router = subtion_router
        self.db_handler = db_handler

        self.router.callback_query.register(self.cmd_subtion, F.data.startswith("subscription"))
        self.router.callback_query.register(self.top_up, F.data == "top_up")
        self.router.callback_query.register(self.select_method, F.data.startswith("method:"))
        self.router.callback_query.register(self.confirm_payment, F.data.startswith("confirm_payment:"))
        self.router.callback_query.register(self.payment, F.data == "payment")
        self.router.callback_query.register(self.pricing, F.data == "pricing")
        self.router.callback_query.register(self.confirm_buy, F.data.startswith("confirm_buy:"))
        self.router.callback_query.register(self.buy, F.data == "buy")

    async def cmd_subtion(self, callback):
        balance = self.db_handler.get_user_balance(callback.from_user.username)
        if callback.data.split(":")[-1] == 'back':
            method = callback.message.edit_text
        else:
            method = callback.message.answer

        time_left = self.db_handler.get_access_expiry(callback.from_user.username)
        access = f'\n{self.format_timedelta_until(time_left)}' if time_left else ''
        await method(f"💰 Ваш текущий баланс: *{balance}*{access}", reply_markup=balance_menu, parse_mode='Markdown')
        await callback.answer()


    async def top_up(self, callback, state):
        sent = await callback.message.edit_text("💳 Выберите способ пополнения:", reply_markup=payment_methods_menu)
        await callback.answer()
        asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def select_method(self, callback, state):
        await disable_msg_timeout(state)

        method = callback.data.split(":")[1]

        if method == 'back':
            data = await state.get_data()
            method = data.get("method")

        await state.update_data(method=method)
        sent = await callback.message.edit_text(
            f"💳 Выбран способ пополнения: `{method}`. Укажите сумму оплаты",
            reply_markup=money_to_pay_menu, parse_mode="Markdown"
        )

        await callback.answer()
        asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def confirm_payment(self, callback, state):
        await disable_msg_timeout(state)
        money = int(callback.data.split(":")[1])
        await state.update_data(money=money)

        sent = await callback.message.edit_text("Подтвердите оплату:", reply_markup=confirm_payment_menu)
        await callback.answer()

        asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def payment(self, callback, state):
        await disable_msg_timeout(state)

        data = await state.get_data()
        method = data.get("method")
        money = int(data.get("money"))

        # TODO
        self.db_handler.pay(callback.from_user.username, money)
        await callback.message.edit_text(f"🎉 Оплата прошла успешно! {method} {money}", reply_markup=default_menu)


    async def pricing(self, callback, state):
        await disable_msg_timeout(state)

        await callback.message.edit_text("📊 Вот мои тарифы:", reply_markup=pricing_menu)
        await callback.answer()

    async def confirm_buy(self, callback, state):
        _, name, price, once, days = callback.data.split(":")
        once = once == 'True'
        once_str = ' Одноразовый!' if once else ''

        if (self.db_handler.tarif_was(callback.from_user.username, tarif_name=name) and once) or not once:
            await state.update_data(buy=name, price=price, days=days)
            subs = ''
            if self.db_handler.is_subscriber(callback.from_user.username):
                subs = f'При покупке нескольких тарифов итоговое время доступа складывается.\n'
            sent = await callback.message.edit_text(
                f"📦 Доступ на {days} дней за {price} рублей.{once_str}\n{subs}Подтвердите покупку:",
                reply_markup=confirm_buy_menu
            )
        else:
            sent = await callback.message.edit_text(
                f"📦 Доступ на {days} дней за {price} рублей.{once_str}\nВы не можете преобрести повторно(",
                reply_markup=default_menu
            )
        await callback.answer()
        asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def buy(self, callback, state):
        data = await state.get_data()
        balance = self.db_handler.get_user_balance(callback.from_user.username)
        money = int(data.get("price"))
        days = int(data.get("days"))
        buy_name = data.get("buy")

        if balance >= money:
            if self.db_handler.buy(callback.from_user.username, buy_name, days, money):
                await callback.message.edit_text("✅ Тариф преобретен, теперь можете подключаться)", reply_markup=default_menu)
                await callback.answer()
            else:
                await callback.message.edit_text("❌ Ошибка бота, попробуйте позже или напишите автору", reply_markup=default_menu)
        else:
            await callback.message.edit_text(f"❌ На балансе недостаточно средств: {balance}", reply_markup=default_menu)



    def format_timedelta_until(self, expiry_time: Optional[datetime]) -> str:
        if expiry_time is None:
            return "Доступ отсутствует"

        now = datetime.now()
        if expiry_time <= now:
            return "Доступ истек"

        delta = expiry_time - now

        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} дн.")
        if hours > 0:
            parts.append(f"{hours} ч.")
        if minutes > 0:
            parts.append(f"{minutes} мин.")
        if not parts:
            parts.append(f"{seconds} сек.")  # если очень мало времени осталось

        return "Ваш доступ активен еще " + " ".join(parts)