from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User

user_list_router = Router()

@user_list_router.message(commands="user_list")
async def list_registered_users(message: types.Message):
    db = next(get_db())
    try:
        # Запрашиваем всех зарегистрированных пользователей
        users = db.query(User).filter(User.is_registered == True).all()

        if not users:
            await message.answer("Нет зарегистрированных пользователей.")
            return

        user_info = "\n".join([f"{user.first_name} {user.last_name} (@{user.username})" for user in users])
        await message.answer(f"Зарегистрированные пользователи:\n{user_info}")

    except Exception as e:
        await message.answer("Произошла ошибка при получении списка пользователей.")
        print(f"Ошибка при запросе пользователей: {e}")
    finally:
        db.close()
