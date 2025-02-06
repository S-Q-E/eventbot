import logging

from aiogram import types, Router, F
from db.database import User, get_db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

user_profile_router = Router()


@user_profile_router.callback_query(F.data.startswith("user_profile"))
async def user_prfile_menu(callback: types.CallbackQuery):
    try:
        db = next(get_db())
        user_id = callback.message.from_user.id
        user = db.query(User).filter_by(user_id=user_id).first()
        logging.info(f"Ошибка в user_profile.py {e}")
        user_menu_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить имя и фамилию", callback_data="change_username")],
        [InlineKeyboardButton(text="Изменить аватар", callback_data="download_avatar")]
    ])
        await callback.message.answer(f"Изменить настройки пользователя: <b>{user.first_name} {user.last_name}</b>",
                                      reply_markup=user_menu_markup)
    except Exception as e:
        await callback.message.answer("Ошибка при доступе к базе данных")
