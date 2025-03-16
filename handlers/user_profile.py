import logging
import os
import time
import io
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.orm import Session

from db.database import User, get_db
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile, InputMediaPhoto, FSInputFile
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
    await callback.message.answer("Пожалуйста, отправьте фото, которое вы хотите установить.")


@user_profile_router.message(F.photo)
async def get_photo(message: types.Message):
    # Берем самое большое фото
    photo = message.photo[-1]
    file_id = photo.file_id
    user_id = message.from_user.id
    bot = message.bot

    try:
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path


        file_bytes = await bot.download_file(file_path)
        file_data = io.BytesIO(file_bytes.read())


        output_dir = "user_avatars"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{user_id}_{int(time.time())}.jpeg"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            f.write(file_data.getvalue())

        db = next(get_db())
        try:
            user = db.query(User).filter_by(id=user_id).first()
            user.photo_file_path = output_path
            user.photo_file_id = file_id
            db.commit()
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="user_profile")]
            ])
            await message.answer("Фото добавлено!", reply_markup=markup)
        except Exception as e:
            logging.error(f"Ошибка при сохранении фото в БД: {e}")
            await message.answer("Ошибка при сохранении фото в базе данных.")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Ошибка при скачивании фото: {e}")
        await message.answer("Ошибка при скачивании фото.")


@user_profile_router.callback_query(F.data == "show_avatar")
async def show_avatar(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    db = next(get_db())

    try:
        user = db.query(User).filter_by(id=user_id).first()

        if user and user.photo_file_path and os.path.exists(user.photo_file_path):

            photo = FSInputFile(user.photo_file_path)
            await callback.message.answer_photo(photo=photo)
        else:

            await callback.message.answer("У вас нет установленного аватара.")
    except Exception as e:
        logging.error(f"Ошибка при попытке показать аватар: {e}")
        await callback.message.answer("Произошла ошибка при попытке показать ваш аватар.")
    finally:
        db.close()  # Закрываем сессию базы данных


@user_profile_router.callback_query(F.data == "show_users_avatar")
async def show_users_avatar(callback: types.CallbackQuery):
    db: Session = next(get_db())
    try:
        users = db.query(User).all()
        users_groups = [users[i:i + 10] for i in range(0, len(users), 10)]
        for group in users_groups:
            media = []
            for user in group:
                if user.photo_file_id:
                    media.append(
                        InputMediaPhoto(media=user.photo_file_id, caption=f"{user.first_name} {user.last_name}")
                    )
                else:
                    logging.warning(f"У пользователя {user.first_name} {user.last_name} отсутствует photo_file_id.")
            if media:
                await callback.message.answer_media_group(media=media)
            else:
                await callback.message.answer("Нет доступных аватарок для отображения.")
    except Exception as e:
        logging.error(f"Ошибка при отправке аватарок: {e}")
        await callback.message.answer("Ошибка при загрузке аватарок.")
    finally:
        db.close()

