import logging

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from db.database import User, get_db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
user_profile_router = Router()


@user_profile_router.callback_query(F.data.startswith("user_profile"))
async def user_profile_menu(callback: types.CallbackQuery):
    try:
        db = next(get_db())
        user_id = callback.from_user.id
        user = db.query(User).filter_by(id=user_id).first()
        user_menu_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏ Изменить имя и фамилию", callback_data=f"change_username_{user_id}")],
        [InlineKeyboardButton(text="📷 Изменить аватар", callback_data="download_avatar")],
        [InlineKeyboardButton(text="📷 Показать мой аватар", callback_data="show_avatar")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])

        await callback.message.answer(f"Изменить настройки пользователя: <b>{user.first_name} {user.last_name}</b>",
                                      reply_markup=user_menu_markup)
    except Exception as e:
        logging.info(f"Ошибка в user_profile.py {e}")
        await callback.message.answer("Ошибка при доступе к базе данных")


class EditProfileStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_photo = State()


@user_profile_router.callback_query(F.data.startswith("change_username"))
async def set_new_username(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await callback.message.answer("Введите новое имя и фамилию через пробел")
    await state.update_data(user_id=user_id)
    await state.set_state(EditProfileStates.waiting_for_username)


@user_profile_router.message(EditProfileStates.waiting_for_username)
async def save_new_username(message: types.Message, state: FSMContext):
    print(message.text)
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="user_profile")]])
    try:
        with next(get_db()) as db:
            first_name, last_name = message.text.split(" ")
            data = await state.get_data()
            user_id = data["user_id"]
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
        logging.info(f"Ошибка в user_profile.py. Код ошибки: {e}")
        await message.answer("Произошла ошибка в базе данных", reply_markup=markup)
    finally:
            db.close()


@user_profile_router.callback_query(F.data == "download_avatar")
async def ask_photo(callback: types.CallbackQuery):
    await callback.message.answer("Пожалуйста отправьте фото, которое вы хотите установить")


@user_profile_router.message(F.photo)
async def get_photo(message: types.Message):
    photo = message.photo[-1]
    file_id = photo.file_id
    user_id = message.from_user.id
    db = next(get_db())
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="user_profile")]])

    try:
        user = db.query(User).filter_by(id=user_id).first()
        user.photo_file_id = file_id
        db.commit()
        await message.answer("Фото добавлено!", reply_markup=markup)
    except Exception as e:
        logging.info(f"Ошибка в базе данных. {e}")
        await message.answer("Ошибка при обработке фото")
    finally:
        db.close()


@user_profile_router.callback_query(F.data == "show_avatar")
async def show_avatar(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="user_profile")]])
    db = next(get_db())
    try:
        user = db.query(User).filter_by(id=user_id).first()
        photo_id = user.photo_file_id
        await callback.message.answer_photo(photo_id, reply_markup=markup)
    except Exception as e:
        logging.info(f"Ошибка в функции show_avatar в файле {__name__} {e}")
        await callback.message.answer("Ошибка при загрузке фото")
    finally:
        db.close()

