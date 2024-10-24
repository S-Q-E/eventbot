import logging
from aiogram import BaseMiddleware
from db.database import get_db, User


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            # Проверка на то, является ли событие сообщением
            user_id = event.from_user.id if hasattr(event, 'from_user') else None
            if not user_id:
                logging.warning("Событие не имеет пользователя.")
                return await handler(event, data)

            db = next(get_db())
            user = db.query(User).filter_by(id=user_id).first()

            # Исключения для команд/событий, которые можно выполнять без регистрации
            allowed_commands = ['events_list', 'start', 'start_reg']
            allowed_callbacks = ['events_list', 'start_reg', 'start_reg']

            # Если это команда (например, текстовое сообщение, начинающееся с "/")
            if event.text and event.text.lstrip("/").split()[0] in allowed_commands:
                return await handler(event, data)

            # Если это callback-запрос
            if hasattr(event, 'data') and event.data in allowed_callbacks:
                return await handler(event, data)

            # Проверка регистрации пользователя
            if user or user.is_registered:
                # Пользователь зарегистрирован, продолжаем выполнение хэндлера
                return await handler(event, data)
            else:
                # Если пользователь не зарегистрирован, отправляем его на регистрацию
                await event.answer("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.")
                return
        except Exception as e:
            logging.error(f"Ошибка в Middleware: {e}")
            await event.answer("Произошла ошибка. Попробуйте позже.")
            return
