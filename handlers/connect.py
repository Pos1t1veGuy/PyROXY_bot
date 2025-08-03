import os
from typing import *
from aiogram import Router, F
from keyboards import cipher_buttons, select_user_key, default_menu
from aiogram.fsm.state import StatesGroup, State
from functools import wraps
import random
import string
import hashlib

from pyperclip import is_available


class KeyInput(StatesGroup):
    waiting_for_key = State()


connect_router = Router()


class ConnectRouter:
    def __init__(self,
                 is_subscriber: Callable[[str, str], bool],
                 save_key: Callable[[str, str], bool],
                 find_key: Callable[[str, str], bool]):
        global connect_router
        self.router = connect_router
        self.cipher_type = None
        self.is_subscriber = is_subscriber
        self.save_key = save_key
        self.find_key = find_key

        self.router.callback_query.register(self.cmd_connect, F.data == "connect")
        self.router.callback_query.register(self.input_key, F.data.startswith("cipher:"))
        self.router.message.register(self.key_input_received, KeyInput.waiting_for_key)
        self.router.callback_query.register(self.generate_key, F.data == "generate_new_key")
        self.router.callback_query.register(self.find_last_key, F.data == "use_last_key")



    async def cmd_connect(self, callback):
        await self.subscriber_only(callback)
        await callback.message.answer("🔒 Выберите тип шифрования:", reply_markup=cipher_buttons)
        await callback.answer()


    async def input_key(self, callback, state):
        await self.subscriber_only(callback)

        self.cipher_type = callback.data.split(":", 1)[1]
        await callback.message.answer(f"✅ Вы выбрали: {self.cipher_type}")
        await callback.message.answer(
            "А теперь укажите ключ шифрования (просто строка с буквами):", reply_markup=select_user_key
        )
        await state.set_state(KeyInput.waiting_for_key)
        await callback.answer()

    async def generate_key(self, callback, state):
        await self.subscriber_only(callback)

        new_key = self.generate_cipher_key().hex()
        if self.save_key(callback.from_user.username, new_key):
            await callback.message.answer(f"✅ Сгенерировала новый ключ: ```{new_key}```",
                                          reply_markup=default_menu, parse_mode='Markdown')
        else:
            await message.answer(
                "❌ Ошибка создания ключа. Попробуйте позже.", reply_markup=default_menu
            )
        await callback.answer()

    async def find_last_key(self, callback, state):
        await self.subscriber_only(callback)

        key = self.find_key(callback.from_user.username)
        if key:
            await callback.message.answer(f"✅ Используем прошлый ключ: ```{key}```",
                                          reply_markup=default_menu, parse_mode='Markdown')
        else:
            await message.answer(
                "❌ Прошлый ключ не найден.", reply_markup=default_menu
            )
        await callback.answer()


    async def key_input_received(self, message, state):
        await self.subscriber_only(message)
        key = message.text.strip()

        is_valid, msg = self.validate_cipher_key(key)
        if not is_valid:
            await message.answer(f'❌ Ошибка: {msg}', reply_markup=default_menu)
            return

        hex_key = key.hex()
        if self.save_key(message.from_user.username, hex_key):
            await message.answer(f"✅ Ключ сохранен, вот его hex формат: {hex_key}", reply_markup=default_menu)
        else:
            await message.answer(
                "❌ Ошибка создания ключа. Попробуйте позже.", reply_markup=default_menu
            )
        await state.clear()



    def validate_cipher_key(self, key: str) -> Tuple[bool, str]:
        available_chars = string.ascii_letters + string.digits + '_-'

        true_chars = [(char in available_chars) for char in key]
        if all(true_chars):
            match self.cipher_type:
                case "ChaCha20-Poly1305":
                    return (len(key) == 32,
                        'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-] длиной в 32 символа. Попробуйте снова')
                case "ChaCha20-Poly1305":
                    return (len(key) in [16,24,32],
                        'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-] длиной в 16/24/32 символа. Попробуйте снова')
                case "ChaCha20-Poly1305":
                    return (len(key) in [16,24,32],
                        'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-] длиной в 16/24/32 символа. Попробуйте снова')
                case _:
                    return False, f'Ошибка валидации ключа {self.cipher_type}. Попробуйте позже'

        else:
            invalid_chars = [f'{i}: {key[i]}\n' for i, char in enumerate(true_chars) if not char][:20]
            return False, (
                f'ключ должен состоять из символов [a-z]+[0-9]+[_]+[-];\n\n|>  {key}  <|\n\n'
                'Неправильные символы:\n\n' + ''.join(invalid_chars)
            )

    def generate_cipher_key(self) -> str:
        return os.urandom(32)


    async def subscriber_only(self, event):
        if not self.is_subscriber(event.from_user.username):
            text = "❌ Для данного действия необходимо преобрести подписку"
            if isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=balance_menu)
            elif isinstance(event, Message):
                await event.answer(text, reply_markup=balance_menu)