from functools import wraps
from aiogram import types
from db.database import get_db, User


def registration_required(handler):
    @wraps(handler)
    async def wrapper(event: types.Message, *args, **kwargs):
        db = next(get_db())
        user = db.query(User).filter_by(id=event.from_user.id).first()

        if user and user.is_registered:
            return await handler(event, *args, **kwargs)
        else:
            await event.answer("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.")
            return

    return wrapper
