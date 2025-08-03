from typing import *
from aiogram import Router, F
from keyboards import cipher_buttons, select_user_key, default_menu, how_to_connect, balance_menu
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import BufferedInputFile
import random
import string
import asyncio
import os
import hashlib


class KeyInput(StatesGroup):
    waiting_for_key = State()


connect_router = Router()


class ConnectRouter:
    def __init__(self,
                 server_host: 'str',
                 is_subscriber: Callable[[str, str], bool],
                 save_key: Callable[[str, str], bool],
                 save_cipher: Callable[[str, str], bool],
                 save_password: Callable[[str, str], bool],
                 find_key: Callable[[str], str],
                 find_cipher: Callable[[str], str],
                 find_password: Callable[[str, str], bool]):

        global connect_router
        self.router = connect_router

        self.host = server_host
        self.is_subscriber = is_subscriber
        self.save_key = save_key
        self.save_password = save_password
        self.save_cipher = save_cipher
        self.find_key = find_key
        self.find_password = find_password
        self.find_cipher = find_cipher

        self.router.callback_query.register(self.cmd_connect, F.data == "connect")
        self.router.callback_query.register(self.input_key, F.data.startswith("cipher:"))
        self.router.callback_query.register(self.cancel, F.data == 'cancel')
        self.router.message.register(self.key_input_received, KeyInput.waiting_for_key)
        self.router.callback_query.register(self.generate_key, F.data == "generate_new_key")
        self.router.callback_query.register(self.find_last_key, F.data == "use_last_key")
        self.router.callback_query.register(self.connect_guide, F.data == "connect_guide")



    async def cmd_connect(self, callback, state):
        await self.subscriber_only(callback)
        sent = await callback.message.answer("🔒 Выберите тип шифрования:", reply_markup=cipher_buttons)
        await callback.answer()

        asyncio.create_task(self._msg_timeout(state, sent, callback.bot))


    async def generate_key(self, callback, state):
        await self.subscriber_only(callback)
        await self._disable_msg_timeout(state)

        new_key = self.generate_cipher_key().hex()
        if self.save_key(callback.from_user.username, new_key):
            await callback.message.edit_text(f"✅ Сгенерировала новый ключ: ```{new_key}```",
                                          reply_markup=how_to_connect, parse_mode='Markdown')
        else:
            await message.edit_text(
                "❌ Ошибка создания ключа. Попробуйте позже.", reply_markup=default_menu
            )
        await callback.answer()

    async def find_last_key(self, callback, state):
        await self.subscriber_only(callback)
        await self._disable_msg_timeout(state)

        key = self.find_key(callback.from_user.username)
        if key:
            await callback.message.edit_text(f"✅ Используем прошлый ключ: ```{key}```",
                                          reply_markup=how_to_connect, parse_mode='Markdown')
        else:
            await message.edit_text(
                "❌ Прошлый ключ не найден.", reply_markup=default_menu
            )
        await callback.answer()

    async def input_key(self, callback, state):
        await self.subscriber_only(callback)
        await self._disable_msg_timeout(state)

        cipher_type = callback.data.split(":", 1)[1]
        self.save_password(
            callback.from_user.username,
            random.choices(string.ascii_letters + string.digits, k=random.randint(8,32))
        )

        self.save_cipher(callback.from_user.username, cipher_type)
        msg = await callback.message.edit_text(
            f"✅ `{cipher_type}`\nА теперь укажите **ключ шифрования** (просто строка с буквами):",
            reply_markup=select_user_key, parse_mode='Markdown'
        )
        await state.update_data(cipher_type=cipher_type, last_msg_id=callback.message.message_id)
        await state.set_state(KeyInput.waiting_for_key)
        await callback.answer()


    async def cancel(self, callback, state):
        try:
            await callback.message.edit_text(
                text="❌ Операция отменена",
                reply_markup=default_menu
            )
        except (TelegramBadRequest, TelegramAPIError):
            pass


    async def key_input_received(self, message, state):
        await self.subscriber_only(message)
        key = message.text.strip()

        data = await state.get_data()
        cipher_type = data.get("cipher_type")
        last_msg_id = data.get("last_msg_id")

        is_valid, msg = self.validate_cipher_key(cipher_type, key)
        if not is_valid:
            await message.answer(f'❌ Ошибка: {msg}', reply_markup=default_menu)
            return

        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except (TelegramBadRequest, TelegramAPIError):
            pass

        hex_key = key.encode().hex()
        if self.save_key(message.from_user.username, hex_key):
            await message.answer(f"✅ Ключ сохранен, вот его hex формат: `{hex_key}`",
                                 reply_markup=how_to_connect, parse_mode='Markdown')
        else:
            await message.answer(
                "❌ Ошибка создания ключа. Попробуйте позже.", reply_markup=default_menu
            )
        await state.clear()


    async def connect_guide(self, callback, state):
        username = callback.from_user.username
        if self.is_subscriber(username):
            key = self.find_key(username)
            password = self.find_password(username)
            cipher = self.cipher_to_parameter(self.find_cipher(username))
            profile_data = f'host={self.host}\nusername={username}\npassword={password}\nkey={key}\ncipher={cipher}'.encode()

            await callback.message.answer_document(
                document=BufferedInputFile(profile_data, filename="profile.pyroxy"),
                caption=(
                    "🔐 Инструкция по подключению:\n\n"
                    "1️⃣ Поместите файл `profile.pyroxy` в папку с PyROXY-клиентом.\n"
                    "2️⃣ Запустите `console_client.exe` или `no_console_client.exe`.\n\n"
                    "⚠️ Файл содержит:\n"
                    "• Ваш ключ авторизации\n"
                    "• Пароль\n"
                    "• Настройки шифрования\n\n"
                    "🚫 Будьте осторожны!\n"
                    "Если файл попадёт в чужие руки, злоумышленники смогут использовать ваш аккаунт.\n"
                    "Я не несу ответственности за компрометацию данных и за трафик, проходящий через VPN.\n"
                ),
                reply_markup=default_menu, parse_mode='Markdown'
            )
        else:
            await message.answer("⚠ Чтобы пользоваться VPN нужно преобрести подписку (либо воспользоваться бесплатным"
                                 "Трехдневным периодом, но это секрет)", reply_markup=balance_menu)

        await callback.answer()


    def validate_cipher_key(self, cipher_type: str, key: str) -> Tuple[bool, str]:
        available_chars = string.ascii_letters + string.digits + '_-'

        true_chars = [(char in available_chars) for char in key]
        if all(true_chars):
            match cipher_type:
                case "ChaCha20-Poly1305":
                    return (len(key) == 32,
                        'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-] длиной в 32 символа. Попробуйте снова')
                case "AES_CTR":
                    return (len(key) in [16,24,32],
                        'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-] длиной в 16/24/32 символа. Попробуйте снова')
                case "AES_CBC":
                    return (len(key) in [16,24,32],
                        'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-] длиной в 16/24/32 символа. Попробуйте снова')
                case _:
                    return False, f'в валидации ключа {cipher_type}. Попробуйте позже'

        else:
            invalid_chars = [f'{i}: {key[i]}\n' for i, char in enumerate(true_chars) if not char][:20]
            return False, (
                f'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-];\n\n|>  {key}  <|\n\n'
                'Неправильные символы:\n\n' + ''.join(invalid_chars)
            )

    def cipher_to_parameter(self, cipher_type: str) -> str:
        match cipher_type:
            case "ChaCha20-Poly1305":
                return 'chacha20'
            case "AES_CTR":
                return 'aes_ctr'
            case "AES_CBC":
                return 'aes_cbc'
            case _:
                return 'none'

    def generate_cipher_key(self) -> str:
        return os.urandom(32)

    async def _msg_timeout(self, state, sent, bot, timeout=60*30):
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

    async def _disable_msg_timeout(self, state):
        await state.update_data(
            last_send_time=-1
        )

    async def subscriber_only(self, event):
        if not self.is_subscriber(event.from_user.username):
            text = "❌ Для данного действия необходимо преобрести подписку"
            if isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=balance_menu)
            elif isinstance(event, Message):
                await event.answer(text, reply_markup=balance_menu)