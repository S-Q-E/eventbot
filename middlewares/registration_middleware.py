import logging
from aiogram import BaseMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from db.database import get_db, User


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            # Определяем пользователя из события
            user_id = event.from_user.id if hasattr(event, 'from_user') else None
            if not user_id:
                logging.warning("Событие не имеет пользователя.")
                return await handler(event, data)

            db = next(get_db())
            user = db.query(User).filter_by(id=user_id).first()

            # Если пользователь не найден в базе данных
            if not user:
                register_button = InlineKeyboardButton(text="Регистрация", callback_data="start_reg")
                markup = InlineKeyboardMarkup(inline_keyboard=[[register_button]])

                # Отправляем сообщение в зависимости от типа события (Message или CallbackQuery)
                if isinstance(event, Message):
                    await event.answer("Вы не зарегистрированы", reply_markup=markup)
                elif isinstance(event, CallbackQuery):
                    await event.message.answer("Вы не зарегистрированы", reply_markup=markup)

                return

            # Исключения для команд/событий, которые можно выполнять без регистрации
            allowed_commands = ['events_list', 'start', 'start_reg']
            allowed_callbacks = ['events_list', 'start_reg']

            # Если это команда (например, текстовое сообщение, начинающееся с "/")
            if isinstance(event, Message) and event.text.lstrip("/").split()[0] in allowed_commands:
                return await handler(event, data)

            # Если это callback-запрос
            if isinstance(event, CallbackQuery) and event.data in allowed_callbacks:
                return await handler(event, data)

            # Проверка регистрации пользователя
            if user.is_registered:  # Теперь эта проверка не будет выполнена, если user == None
                return await handler(event, data)
            else:
                reg_button = InlineKeyboardButton(text="Регистрация", callback_data="start_reg")
                markup = InlineKeyboardMarkup(inline_keyboard=[[reg_button]])

                if isinstance(event, Message):
                    await event.answer("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.", reply_markup=markup)
                elif isinstance(event, CallbackQuery):
                    await event.message.answer("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.",
                                               reply_markup=markup)

                return
        except Exception as e:
            logging.error(f"Ошибка в Middleware: {e}")

            if isinstance(event, Message):
                await event.answer(f"Произошла ошибка. Попробуйте позже.\n{e}")
            elif isinstance(event, CallbackQuery):
                await event.message.answer(f"Произошла ошибка. Попробуйте позже.\n{e}")

            return
