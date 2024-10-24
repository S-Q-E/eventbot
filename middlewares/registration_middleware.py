from aiogram import BaseMiddleware
from aiogram.types import Update
from db.database import get_db, User


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        db = next(get_db())

        user = db.query(User).filter_by(id=user_id).first()

        # Исключения для команд/событий, которые можно выполнять без регистрации
        allowed_commands = ['events_list', 'start']
        allowed_callbacks = ['events']

        # Проверка команды или коллбэка
        if event.text and event.text.lstrip("/").split()[0] in allowed_commands:
            return await handler(event, data)

        if hasattr(event, 'data') and event.data in allowed_callbacks:
            return await handler(event, data)

        if user and user.is_registered:
            # Пользователь зарегистрирован, продолжаем выполнение хэндлера
            return await handler(event, data)
        else:
            # Если пользователь не зарегистрирован, отправляем его на регистрацию
            await event.answer("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.")
            return
