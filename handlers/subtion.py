from typing import *
from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
import asyncio

from ..keyboards import (balance_menu, default_menu, payment_methods_menu, pricing_menu, money_to_pay_menu,
                       confirm_buy_menu, confirm_payment_menu, confirm_not_invoice_menu)
from .utils import msg_timeout, disable_msg_timeout, format_username


class DetailsInput(StatesGroup):
    waiting_for_key = State()


subtion_router = Router()


class SubtionRouter:
    def __init__(self, db_handler: 'Handler', payment_methods: Dict[str, str], author_id: int,
                 after_not_invoice_payment: Optional[Callable[[str, int, str], None]] = None):

        global subtion_router
        self.router = subtion_router
        self.payment_methods = payment_methods
        self.after_not_invoice_payment = after_not_invoice_payment
        self.db_handler = db_handler
        self.author_id = author_id

        self.router.callback_query.register(self.cmd_subtion, F.data.startswith("subscription"))
        self.router.callback_query.register(self.top_up, F.data == "top_up")
        self.router.callback_query.register(self.select_method, F.data.startswith("method:"))
        self.router.callback_query.register(self.confirm_payment, F.data.startswith("confirm_payment:"))
        self.router.message.register(self.details_input_received, DetailsInput.waiting_for_key)
        self.router.callback_query.register(self.payment, F.data == "payment")

        self.router.callback_query.register(self.pricing, F.data == "pricing")
        self.router.callback_query.register(self.confirm_buy, F.data.startswith("confirm_buy:"))
        self.router.callback_query.register(self.buy, F.data == "buy")

    async def cmd_subtion(self, callback):
        balance = await self.db_handler.get_user_balance(format_username(callback))
        if callback.data.split(":")[-1] == 'back':
            method = callback.message.edit_text
        else:
            method = callback.message.answer

        time_left = await self.db_handler.get_access_expiry(format_username(callback))
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
        method_data = self.payment_methods[method]

        if method_data['invoice']:
            sent = await callback.message.edit_text(
                f"💳 Выбран способ пополнения: `{method}`. Укажите сумму оплаты",
                reply_markup=money_to_pay_menu, parse_mode="Markdown"
            )
        else:
            sent = await callback.message.edit_text(
                f"💳 Выбран способ пополнения: `{method}`. Чтобы пополнить счет бота необходимо перевести нужную сумму "
                f"на счет администрации, деньги будут начислены в течение нескольких часов. Вот реквизиты: \n\n"
                f"`{method_data['token']}`\n\nПодтвердите, что деньги были отправлены вами на указанный счет:",
                reply_markup=confirm_not_invoice_menu, parse_mode="Markdown"
            )

        await callback.answer()
        asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def confirm_payment(self, callback, state):
        await disable_msg_timeout(state)
        money = callback.data.split(":")[1]
        await state.update_data(money=money)

        data = await state.get_data()
        method = data.get("method")
        method_data = self.payment_methods[method]

        if method_data['invoice']:
            sent = await callback.message.edit_text("Подтвердите оплату:", reply_markup=confirm_payment_menu)
        else:
            sent = await callback.message.edit_text(
                "✏️ Пожалуйста, введите реквизиты, с которых был или будет отправлен платёж.\n"
                "Например:\n"
                "• Номер карты\n"
                "• Номер телефона, привязанного к карте\n\n"
                "Проверьте введенные данные перед отправкой, в случае возникновения проблем, возможна связь с админом из"
                " главного меню.",
                reply_markup=default_menu
            )
            await state.update_data(bot_message_id=sent.message_id)
            await state.set_state(DetailsInput.waiting_for_key)

        await callback.answer()

        asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def details_input_received(self, message, state):
        payment_id = await self.db_handler.add_pending_payment(format_username(message), message.from_user.id,
                                                         message.text.strip(), do_after=self.after_not_invoice_payment)
        try:
            await message.delete()
        except Exception:
            pass

        data = await state.get_data()
        bot_message_id = data.get("bot_message_id")
        text = f"🎉 Ожидайте поступления денег на счет... Зачисление должно произойти в течение нескольких часов"

        if bot_message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    text=text,
                    reply_markup=default_menu
                )
            except:
                await message.answer(text, reply_markup=default_menu)
        else:
            await message.answer(text, reply_markup=default_menu)

        try:
            await message.bot.send_message(
                self.author_id,
                f"💰 Новый запрос на пополнение!\n"
                f"> {payment_id}\n"
                f"👤 Пользователь: @{message.from_user.username} (ID: {message.from_user.id})\n"
                f"📄 Детали: {message.text.strip()}"
            )
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")

        await state.clear()

    async def payment(self, callback, state):
        await disable_msg_timeout(state)

        data = await state.get_data()
        method = data.get("method")
        method_data = self.payment_methods[method]

        money = int(data.get("money"))
        # TODO: доделать оплату инвойсами
        await callback.bot.send_invoice(
            chat_id=callback.message.chat.id,
            title="Оплата тарифа PyROXY",
            description=f"Метод оплаты: {method}",
            payload="custom_payload_data",
            provider_token=self.payment_methods[method],
            currency="RUB",
            prices=[
                # types.LabeledPrice(label="Пополнение баланса", amount=money * 100)
            ],
            start_parameter=f"proxy-{money}r",
            is_flexible=False
        )
        await self.db_handler.pay(format_username(callback), money)
        await callback.message.edit_text(f"🎉 Оплата прошла успешно! {method} {money}", reply_markup=default_menu)

    async def pricing(self, callback, state):
        await disable_msg_timeout(state)

        await callback.message.edit_text("📊 Вот мои тарифы:", reply_markup=pricing_menu)
        await callback.answer()

    async def confirm_buy(self, callback, state):
        _, name, price, once, days = callback.data.split(":")
        once = once == 'True'
        once_str = ' Одноразовый!' if once else ''

        if (await self.db_handler.tarif_was(format_username(callback), tarif_name=name) and once) or not once:
            await state.update_data(buy=name, price=price, days=days)
            subs = ''
            if await self.db_handler.is_subscriber(format_username(callback)):
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
        balance = await self.db_handler.get_user_balance(format_username(callback))
        money = int(data.get("price"))
        days = int(data.get("days"))
        buy_name = data.get("buy")

        if balance >= money:
            if await self.db_handler.buy(format_username(callback), buy_name, days, money):
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
            parts.append(f"{seconds} сек.")

        return "Ваш доступ активен еще " + " ".join(parts)