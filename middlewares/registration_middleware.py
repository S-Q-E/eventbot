import logging
from aiogram import BaseMiddleware
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.database import get_db, User

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            # Проверяем, что событие содержит пользователя
            user_id = getattr(event.from_user, 'id', None)
            if not user_id:
                logging.warning("Событие не содержит пользователя.")
                return await handler(event, data)

            # Получаем сессию базы данных и ищем пользователя
            db = next(get_db())
            user = db.query(User).filter_by(id=user_id).first()

            if not user:
                # Если пользователя нет, создаем запись и отправляем сообщение о необходимости регистрации
                new_user = User(id=user_id, is_registered=False)
                db.add(new_user)
                db.commit()

                register_button = InlineKeyboardButton(text="Регистрация", callback_data="start_reg")
                markup = InlineKeyboardMarkup(inline_keyboard=[[register_button]])
                await event.answer("Вы не зарегистрированы", reply_markup=markup)

                # Возвращаем после отправки сообщения о регистрации
                return

            # Разрешенные команды и callback'и для незарегистрированных пользователей
            allowed_commands = ['events_list', 'start', 'start_reg']
            allowed_callbacks = ['events_list', 'start_reg']

            # Если это команда, проверяем, что она разрешена для незарегистрированных пользователей
            if hasattr(event, 'text') and event.text.lstrip("/").split()[0] in allowed_commands:
                return await handler(event, data)

            # Если это callback-запрос, проверяем, что он разрешен для незарегистрированных пользователей
            if hasattr(event, 'data') and event.data in allowed_callbacks:
                return await handler(event, data)

            # Если пользователь существует, но не зарегистрирован, отправляем только одно сообщение о регистрации
            if not user.is_registered:
                register_button = InlineKeyboardButton(text="Регистрация", callback_data="start_reg")
                markup = InlineKeyboardMarkup(inline_keyboard=[[register_button]])
                await event.answer("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.", reply_markup=markup)
                return

            # Если пользователь зарегистрирован, передаем управление обработчику
            return await handler(event, data)

        except Exception as e:
            logging.error(f"Ошибка в Middleware: {e}")
            await event.answer("Произошла ошибка. Попробуйте позже.")
            return
