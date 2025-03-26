import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import asc

from db.database import get_db, User
from aiogram.fsm.state import StatesGroup, State

delete_user_router = Router()


class DeleteUserState(StatesGroup):
    waiting_for_user_id = State()


@delete_user_router.callback_query(F.data == "all_users")
async def list_registered_users(callback: types.CallbackQuery, state: FSMContext):
    db = next(get_db())

    try:
        users = db.query(User).order_by(asc(User.first_name), asc(User.last_name)).all()

        if not users:
            await callback.message.answer("Нет пользователей для отображения.")
            return

        user_info = "Список пользователей:\n"
        for index, user in enumerate(users, 1):
            user_info += f"{index}. ID: <code>{user.id}</code>, {user.first_name} {user.last_name}\n"

        await callback.message.answer(text=user_info)

        await callback.message.answer(text="Введите ID пользователя которого хотите удалить\n")

    except Exception as e:
        await callback.message.answer("Произошла ошибка при получении списка пользователей.")
        print(f"Ошибка при запросе пользователей: {e}")
    finally:
        db.close()


@delete_user_router.message(DeleteUserState.waiting_for_user_id)
async def delete_user_by_id(message: types.Message):
    user_id = int(message.text)
    db = next(get_db())
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            await message.answer("Пользователь не найдет")
        db.delete(user)
        db.commit()
        await message.answer("Пользователь успешно удален!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Назад", callback_data="admin_panel")
        ]]))
        db.close()
    except Exception as e:
        logging.info(f"Произошла ошибка в {__name__} {e}")
        await message.answer("Произошла ошибка")
    finally:
        db.close()


@delete_user_router.callback_query(F.data.startswith("delete_user_"))
async def delete_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[-1])
    db = next(get_db())

    try:
        # Находим и удаляем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await callback.message.answer("Пользователь не найден.")
            return

        db.delete(user)
        db.commit()

        await callback.answer(f"Пользователь {user.first_name} удалён.", show_alert=True)
        await callback.message.edit_text(f"Пользователь {user.first_name} удален.")
    except Exception as e:
        await callback.answer("Ошибка при удалении пользователя.")
        print(f"Ошибка удаления пользователя: {e}")
    finally:
        db.close()
