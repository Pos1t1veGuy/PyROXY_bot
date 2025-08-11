from typing import *
from aiogram import Router, F
from keyboards import (cipher_buttons_menu, select_user_key_menu, default_menu, how_to_connect_menu, balance_menu,
                       select_tarif_menu, password_menu)
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import BufferedInputFile, FSInputFile, Message, CallbackQuery
import random
import string
import asyncio
import os

from .utils import msg_timeout, disable_msg_timeout


class KeyInput(StatesGroup):
    waiting_for_key = State()


connect_router = Router()


class ConnectRouter:
    def __init__(self,
                 server_host: str,
                 default_server_key: str,
                 ciphers: List[str],
                 db_handler: 'Handler'):

        global connect_router
        self.router = connect_router
        self.db_handler = db_handler
        self.host = server_host
        self.ciphers = ciphers
        self.default_server_key = default_server_key

        # guides
        self.router.callback_query.register(self.connect_guide, F.data == "connect_guide")
        self.router.callback_query.register(self.encryption_guide, F.data == "encryption_guide")

        # password
        self.router.callback_query.register(self.cmd_connect, F.data.startswith("connect"))
        self.router.callback_query.register(self.generate_pw, F.data == "generate_new_pw")
        self.router.callback_query.register(self.find_last_pw, F.data == "use_last_pw")

        # cipher
        self.router.callback_query.register(self.input_key, F.data.startswith("cipher:"))
        self.router.callback_query.register(self.choose_cipher, F.data == "choose_cipher")
        self.router.message.register(self.key_input_received, KeyInput.waiting_for_key)
        self.router.callback_query.register(self.generate_key, F.data == "generate_new_key")
        self.router.callback_query.register(self.find_last_key, F.data == "use_last_key")



    async def cmd_connect(self, callback, state):
        if await self.subscriber_only(callback):
            if callback.data.split(":")[-1] == 'back':
                method = callback.message.edit_text
            else:
                method = callback.message.answer

            sent = await method("🔒 <b>Нужно выбрать пароль</b>, с помощью которого вы будете проходить авторизацию в "
                                "прокси сети.\n\n⚠️ Обратите внимание, что пароль нельзя показывать посторонним!",
                                reply_markup=password_menu, parse_mode='HTML')
            await callback.answer()

            asyncio.create_task(msg_timeout(state, sent, callback.bot))

    async def generate_pw(self, callback, state):
        if await self.subscriber_only(callback):
            await disable_msg_timeout(state)

            new_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(8, 32)))
            self.db_handler.save_password(callback.from_user.username, new_pw)

            await self.choose_cipher(callback, state)

    async def find_last_pw(self, callback, state):
        if await self.subscriber_only(callback):
            await disable_msg_timeout(state)
            pw = self.db_handler.find_password(callback.from_user.username)
            if pw:
                await self.choose_cipher(callback, state)
            else:
                await callback.message.edit_text("❌ Прошлый пароль не найден.", reply_markup=default_menu)


    async def choose_cipher(self, callback, state):
        if await self.subscriber_only(callback):
            sent = await callback.message.edit_text("🔒 <b>Требуется выбрать тип шифрования</b>, которым будет покрываться "
                                                    "ваш трафик.\n\nℹ️ Подробнее о шифровании в главном меню, для"
                                                    "наибольшей скорости поспользуйтесь <b>default</b> (без шифра).",
                                                    reply_markup=cipher_buttons_menu, parse_mode='HTML')
            await callback.answer()

            asyncio.create_task(msg_timeout(state, sent, callback.bot))


    async def generate_key(self, callback, state):
        if await self.subscriber_only(callback):
            await disable_msg_timeout(state)

            new_key = self.generate_cipher_key().hex()
            if self.db_handler.save_key(callback.from_user.username, new_key):
                await callback.message.edit_text(f"✅ Сгенерировала новый ключ: ```{new_key}```",
                                              reply_markup=how_to_connect_menu, parse_mode='Markdown')
            else:
                await message.edit_text(
                    "❌ Ошибка создания ключа. Попробуйте позже.", reply_markup=default_menu
                )
            await callback.answer()

    async def find_last_key(self, callback, state):
        if await self.subscriber_only(callback):
            await disable_msg_timeout(state)

            key = self.db_handler.find_key(callback.from_user.username)
            if key:
                await callback.message.edit_text(f"✅ Используем прошлый ключ: ```{key}```",
                                              reply_markup=how_to_connect_menu, parse_mode='Markdown')
            else:
                await message.edit_text(
                    "❌ Прошлый ключ не найден.", reply_markup=default_menu
                )
            await callback.answer()

    async def input_key(self, callback, state):
        if await self.subscriber_only(callback):
            await disable_msg_timeout(state)

            cipher_type = callback.data.split(":")[1]

            if cipher_type == 'back':
                data = await state.get_data()
                cipher_type = data.get("cipher_type")
            else:
                self.db_handler.save_cipher(callback.from_user.username, cipher_type)

            msg = await callback.message.edit_text(
                f"✅ `{cipher_type}`\nА теперь укажите **ключ шифрования** (просто строка с буквами):",
                reply_markup=select_user_key_menu, parse_mode='Markdown'
            )
            await state.update_data(cipher_type=cipher_type, last_msg_id=callback.message.message_id)
            await state.set_state(KeyInput.waiting_for_key)
            await callback.answer()


    async def key_input_received(self, message, state):
        if await self.subscriber_only(message):
            key = message.text.strip()

            data = await state.get_data()
            cipher_type = data.get("cipher_type")
            last_msg_id = data.get("last_msg_id")

            is_valid, msg = self.validate_cipher_key(cipher_type, key)
            if not is_valid:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=last_msg_id,
                    text=f'❌ Ошибка: {msg}',
                    reply_markup=default_menu)
                return

            hex_key = key.encode().hex()
            if self.db_handler.save_key(message.from_user.username, hex_key):
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=last_msg_id,
                    text=f"✅ Ключ сохранен, вот его hex формат: `{hex_key}`",
                    reply_markup=how_to_connect_menu,
                    parse_mode='Markdown'
                )
            else:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=last_msg_id,
                    text="❌ Ошибка создания ключа. Попробуйте позже.",
                    reply_markup=default_menu
                )
            await state.clear()


    async def connect_guide(self, callback, state):
        username = callback.from_user.username
        if self.db_handler.is_subscriber(username):
            key = self.db_handler.find_key(username)
            password = self.db_handler.find_password(username)
            cipher = self.cipher_to_parameter(self.db_handler.find_cipher(username))
            profile_data = (f'host={self.host}\nusername={username}\npassword={password}\nkey={key}\n'
                            f'cipher={cipher}\ndefault_key={self.default_server_key}').encode()

            await callback.message.answer_document(
                document=BufferedInputFile(profile_data, filename="profile.pyroxy"),
                caption=(
                    "🔐 ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ:\n\n"
                    "1️⃣ Скачайте архив `pyroxy_client.zip` и распакуйте его в любое удобное место, это ваш прокси-клиент.\n"
                    "2️⃣ Поместите файл `profile.pyroxy` в ту же папку, где находится распакованный клиент.\n"
                    "3️⃣ Запустите `console_client.exe` или `no_console_client.exe` в папке клиента.\n\n"
                    "⚠️ Файл `profile.pyroxy` содержит:\n"
                    "• Ваш ключ авторизации\n"
                    "• Пароль\n"
                    "• Настройки шифрования\n\n"
                    "🚫 Будьте осторожны!\n"
                    "Если файл попадёт в чужие руки, злоумышленники смогут использовать ваш аккаунт.\n"
                    "Я не несу ответственности за компрометацию данных и за трафик, проходящий через VPN.\n"
                ),
                reply_markup=default_menu, parse_mode='Markdown'
            )
            await callback.message.answer_document(
                document=FSInputFile("pyroxy_client.zip"),
                caption="📦 Это клиент PyROXY. Распакуйте архив и следуйте инструкции."
            )
        else:
            await callback.message.answer("⚠ Чтобы пользоваться VPN нужно преобрести платный доступ (либо воспользоваться"
                                          " <b><u>бесплатным трехдневным периодом</u></b>, но это секрет)",
                                          reply_markup=select_tarif_menu, parse_mode="HTML")

        await callback.answer()

    async def encryption_guide(self, callback, state):
        await callback.message.answer("🔒 **ДОСТУПНЫЕ АЛГОРИТМЫ ШИФРОВАНИЯ:**\n\n" + '\n'.join([
                f'*{name}*\n{description}\n' for name, description in self.ciphers.items()
            ]),
            reply_markup=default_menu, parse_mode='Markdown'
        )
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

    async def subscriber_only(self, event) -> bool:
        if not self.db_handler.is_subscriber(event.from_user.username):
            text = "❌ Чтобы использовать эту функцию, активируйте доступ"
            if isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=balance_menu)
            elif isinstance(event, Message):
                await event.answer(text, reply_markup=balance_menu)
            await event.answer()
            return False

        return True