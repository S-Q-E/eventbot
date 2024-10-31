from aiogram import Router, types, F
from db.database import get_db, User
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

# from utils.reg_required import registration_required

set_admin_router = Router()

# # @registration_required
# @admin_settings_router.message(Command("admin_settings"))
# async def admin_set(message:Message, callback_query):
#     pass


@set_admin_router.callback_query(F.data == "set_admin")
@set_admin_router.message(Command("set_admin"))
async def set_admin(callback: types.CallbackQuery):
    db = next(get_db())
    try:
        users = db.query(User).filter(User.is_registered == True).all()

        if not users:
            await callback.message.answer("Нет зарегистрированных пользователей.")
            return

        # Формируем кнопки для каждого пользователя
        for user in users:
            make_admin_button = InlineKeyboardButton(
                text="Сделать админом",
                callback_data=f"make_admin_{user.id}"
            )
            markup = InlineKeyboardMarkup(inline_keyboard=[[make_admin_button]])
            await callback.message.answer(
                f"{user.first_name} {user.last_name} (@{user.username})",
                reply_markup=markup
            )
    except Exception as e:
        await callback.message.answer("Произошла ошибка при получении списка пользователей.")
        print(f"Ошибка при запросе пользователей: {e}")
    finally:
        db.close()


@set_admin_router.callback_query(F.data.startswith("make_admin_"))
async def make_admin(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user and not user.is_admin:
            user.is_admin = True
            db.commit()
            await callback.message.answer(f"{user.username} теперь админ.")
        else:
            await callback.message.answer("Пользователь уже админ или не найден.")
    except Exception as e:
        await callback.message.answer("Произошла ошибка при назначении администратора.")
        print(f"Ошибка при назначении администратора: {e}")
    finally:
        db.close()