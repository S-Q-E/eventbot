import html
from aiogram import Router, types, F
from db.database import get_db, User
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

set_admin_router = Router()


@set_admin_router.callback_query(F.data == "set_admin")
@set_admin_router.message(Command("set_admin"))
async def set_admin(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    with get_db() as db:
        try:
            users = db.query(User).filter(User.is_registered == True).all()
            if not users:
                await callback.message.answer("Нет зарегистрированных пользователей.")
                return

            for user in users:
                delete_admin_btn = InlineKeyboardButton(
                    text="Удалить админа",
                    callback_data=f"delete_admin_{user.id}"
                )
                del_markup = InlineKeyboardMarkup(inline_keyboard=[[delete_admin_btn]])
                safe_first_name = html.escape(user.first_name or "")
                safe_last_name = html.escape(user.last_name or "")
                safe_username = html.escape(user.username or "")
                
                if user.is_admin:
                    await callback.message.answer(f"{safe_first_name} {safe_last_name} @{safe_username}",
                                                  reply_markup=del_markup)
                else:
                    make_admin_button = InlineKeyboardButton(
                        text="Сделать админом",
                        callback_data=f"make_admin_{user.id}"
                    )
                    markup = InlineKeyboardMarkup(inline_keyboard=[[make_admin_button]])
                    await callback.message.answer(
                        f"{safe_first_name} {safe_last_name} (@{safe_username}) - Не админ",
                        reply_markup=markup
                    )

            # Отправляем назад
            back_btn = InlineKeyboardButton(text="↩️", callback_data="admin_panel")
            back_markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
            await callback.message.answer("Вернуться назад", reply_markup=back_markup)

        except Exception as e:
            await callback.message.answer("Произошла ошибка при получении списка пользователей.")
            print(f"Ошибка при запросе пользователей: {e}")


@set_admin_router.callback_query(F.data.startswith("make_admin_"))
async def make_admin(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    user_id = int(callback.data.split("_")[-1])
    with get_db() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and not user.is_admin:
                user.is_admin = True
                safe_username = html.escape(user.username or user.first_name or "Пользователь")
                await callback.message.answer(f"{safe_username} теперь админ.")
            else:
                await callback.message.answer("Пользователь уже админ или не найден.")
        except Exception as e:
            await callback.message.answer("Произошла ошибка при назначении администратора.")
            print(f"Ошибка при назначении администратора: {e}")


@set_admin_router.callback_query(F.data.startswith("delete_admin_"))
async def delete_admin(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    user_id = int(callback.data.split("_")[-1])
    with get_db() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_admin:
                user.is_admin = False
                safe_username = html.escape(user.username or user.first_name or "Пользователь")
                await callback.message.answer(f"{safe_username} теперь отдыхает.")
            else:
                await callback.message.answer("Пользователь уже НЕ админ.")
        except Exception as e:
            await callback.message.answer("Произошла ошибка при удалении администратора.")
            print(f"Ошибка при удалении администратора: {e}")
