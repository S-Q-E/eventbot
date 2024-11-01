from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User
from aiogram.filters import Command

user_list_router = Router()


@user_list_router.callback_query(F.data == "user_list")
async def list_registered_users(callback: types.CallbackQuery):
    db = next(get_db())
    try:
        # Запрашиваем всех зарегистрированных пользователей
        users = db.query(User).filter(User.is_registered == True).all()

        if not users:
            await callback.message.answer("Нет зарегистрированных пользователей.")
            return

        user_info = "\n".join([f"{user.first_name} {user.last_name} (@{user.username} {user.phone_number})" for user in users])
        await callback.message.answer(text=f"Зарегистрированные пользователи:\n{user_info}")

    except Exception as e:
        await callback.message.answer("Произошла ошибка при получении списка пользователей.")
        print(f"Ошибка при запросе пользователей: {e}")
    finally:
        db.close()
