import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import asc
from aiogram.fsm.state import StatesGroup, State

from db.database import get_db, User
from utils.split_message import split_message

logger = logging.getLogger(__name__)
delete_user_router = Router()


to_admin_panel = InlineKeyboardButton(text="В панель админа", callback_data="admin_panel")
markup = InlineKeyboardMarkup(inline_keyboard=[[to_admin_panel]])


class DeleteUserState(StatesGroup):
    waiting_for_user_id = State()


class EditUserStates(StatesGroup):
    waiting_for_user_id = State()


@delete_user_router.callback_query(F.data == "all_users")
async def list_registered_users(callback: types.CallbackQuery, state: FSMContext):
    try:
        with get_db() as db:
            users = db.query(User).order_by(asc(User.first_name), asc(User.last_name)).all()

        if not users:
            await callback.message.answer("Нет пользователей для отображения.")
            return

        user_info = "Список пользователей:\n"
        for index, user in enumerate(users, 1):
            user_info += f"{index}. ID: <code>{user.id}</code>, {user.username} {user.first_name} {user.last_name}\n"

        for chunk in split_message(user_info):
            await callback.message.answer(chunk)

        await callback.message.answer("Введите ID пользователя, которого хотите удалить")
        await state.set_state(DeleteUserState.waiting_for_user_id)
    except Exception as e:
        logger.exception("Ошибка при получении списка пользователей: %s", e)
        await callback.message.answer("Произошла ошибка при получении списка пользователей.")


@delete_user_router.message(DeleteUserState.waiting_for_user_id)
async def delete_user_by_id(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("ID должен быть числом.")
        return

    user_id = int(message.text)

    try:
        with get_db() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                await message.answer("Пользователь не найден")
                return
            db.delete(user)

        await message.answer("Пользователь успешно удален!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Назад", callback_data="admin_panel")
        ]]))
        await state.clear()
    except Exception as e:
        logger.exception("Ошибка удаления пользователя: %s", e)
        await message.answer("Произошла ошибка")


@delete_user_router.callback_query(F.data.startswith("delete_user_"))
async def delete_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[-1])

    try:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                await callback.message.answer("Пользователь не найден.")
                return

            first_name = user.first_name or ""
            db.delete(user)

        await callback.answer(f"Пользователь {first_name} удалён.", show_alert=True)
        await callback.message.edit_text(f"Пользователь {first_name} удален.")
    except Exception as e:
        logger.exception("Ошибка удаления пользователя: %s", e)
        await callback.answer("Ошибка при удалении пользователя.")


@delete_user_router.callback_query(F.data == "edit_user")
async def edit_user(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        with get_db() as db:
            all_users = db.query(User).order_by(asc(User.first_name), asc(User.last_name)).all()

        if not all_users:
            await callback_query.message.answer("Нет доступных пользователей")
            return

        user_list = "\n".join(
            f"▪️ {user.first_name} {user.last_name} ID: <code>{user.id}</code>" for user in all_users
        )

        await callback_query.message.answer(
            "Введите <b>ID и НОВОЕ имя и фамилию</b> пользователя через пробел.\n"
            "Пример: <code>123 Иван Иванов</code>\n\n"
            "Список пользователей:",
            reply_markup=markup,
            parse_mode="HTML"
        )

        for chunk in split_message(user_list):
            await callback_query.message.answer(chunk, parse_mode="HTML")

        await state.set_state(EditUserStates.waiting_for_user_id)
    except Exception as e:
        logger.exception("Ошибка в edit_user: %s", e)
        await callback_query.message.answer("Произошла ошибка. Попробуйте еще раз.")


@delete_user_router.message(EditUserStates.waiting_for_user_id)
async def save_new_username(message: types.Message, state: FSMContext):
    raw = (message.text or "").strip()
    parts = raw.split()

    if len(parts) < 3 or not parts[0].isdigit():
        await message.answer(
            "Неверный формат. Введите: <code>ID Имя Фамилия</code>",
            parse_mode="HTML",
            reply_markup=markup,
        )
        return

    user_id = int(parts[0])
    first_name = parts[1]
    last_name = " ".join(parts[2:])

    try:
        with get_db() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                await message.answer("❗ Пользователь не найден. Проверьте ID.", reply_markup=markup)
                return

            user.first_name = first_name
            user.last_name = last_name

        await message.answer(
            f"✅ Имя пользователя обновлено: {first_name} {last_name}.",
            reply_markup=markup
        )
        await state.clear()
    except Exception as e:
        logger.exception("Ошибка сохранения нового имени: %s", e)
        await message.answer("Произошла ошибка в базе данных", reply_markup=markup)
