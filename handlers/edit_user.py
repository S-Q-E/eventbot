import logging
from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import asc

from db.database import get_db, User

edit_user_router = Router()

to_admin_panel = InlineKeyboardButton(text="В панель админа",
                                      callback_data="admin_panel")
markup = InlineKeyboardMarkup(inline_keyboard=[[to_admin_panel]])


class EditUserStates(StatesGroup):
    waiting_for_user_id = State()


@edit_user_router.callback_query(F.data == "edit_user")
async def edit_user(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        with next(get_db()) as db:
            all_users = db.query(User).order_by(asc(User.first_name), asc(User.last_name)).all()
            if not all_users:
                await callback_query.message.answer("Нет доступных пользователей")

            user_list = "\n".join(
                f"▪️{user.first_name} {user.last_name} ID: <b>{user.id}</b>" for user in all_users
                )
            await callback_query.message.answer(f"Отлично, давайте отредактируем имя и фамилию пользователя\n"
                                                f"Введите <b>ID и НОВОЕ имя и фамилию</b> пользователя через пробел\n"
                                                f"Высылаю список пользователей:\n\n {user_list}",
                                                reply_markup=markup)
            await state.set_state(EditUserStates.waiting_for_user_id)
    except Exception as e:
        logging.info(f"Ошибка в edit_user.py {e}")
        await callback_query.message.answer(f"Произошла ошибка. Попробуйте еще раз.")
    finally:
        db.close()


@edit_user_router.message(EditUserStates.waiting_for_user_id)
async def save_new_username(message: types.Message, state: FSMContext):
    try:
        with next(get_db()) as db:
            user_id, first_name, last_name = message.text.split(" ")
            user = db.query(User).filter_by(id=int(user_id)).first()
            if user:
                user.first_name = first_name
                user.last_name = last_name
                db.commit()
                await message.answer(f"✅ Имя пользователя успешно обновлено на {user.first_name} {user.last_name}.",
                                     reply_markup=markup)
            else:
                await message.answer("❗ Пользователь не найден. Проверьте правильность данных", reply_markup=markup)
            await state.clear()
    except Exception as e:
        logging.info(f"Ошибка в edit_user.py. Код ошибки: {e}")
        await message.answer("Произошла ошибка в базе данных", reply_markup=markup)
    finally:
            db.close()



