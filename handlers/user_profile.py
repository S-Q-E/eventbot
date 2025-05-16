import logging
import os
import time
import io
from aiogram import types, Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from db.database import User, get_db, Category
from aiogram_widgets.pagination import KeyboardPaginator
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
        [InlineKeyboardButton(text="📷 Добавить фото", callback_data="download_avatar")],
        [InlineKeyboardButton(text="📷 Показать моё фото", callback_data="show_avatar")],
        [InlineKeyboardButton(text="❤️Мои интересы", callback_data="interests")],
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
async def ask_photo(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Пожалуйста, отправьте фото, которое вы хотите установить.")
    await state.set_state(EditProfileStates.waiting_for_photo)


@user_profile_router.message(EditProfileStates.waiting_for_photo, F.photo)
async def get_photo(message: types.Message):
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


@user_profile_router.callback_query(F.data == "user_help")
async def help_message(callback: CallbackQuery):
    back_btn = InlineKeyboardButton(text="Назад", callback_data="main_menu")
    markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
    await callback.message.answer("📝 Как записаться на событие: \n"
                                  "1. Выберите событие из списка\n"
                                  "2. Нажмите кнопку «Записаться» ✅.\n"
                                  "3. Оплатите участие по СБП\n"
                                  "Поздравляю! Вы смогли записаться на желаемое событие!\n"
                                  "Возникли трудности? Напиши @Kozlov_Vasily",
                                  reply_markup=markup)


from sqlalchemy.orm import joinedload

@user_profile_router.callback_query(F.data == "interests")
async def show_interest_categories(callback: types.CallbackQuery):
    # 1) Новая сессия
    db = next(get_db())
    try:
        # 2) Сразу подгружаем связи interests
        user = (
            db.query(User)
              .options(joinedload(User.interests))
              .filter(User.id == callback.from_user.id)
              .first()
        )
        if not user:
            return await callback.answer("Пользователь не найден", show_alert=True)

        cats = db.query(Category).order_by(Category.name).all()

        builder = InlineKeyboardBuilder()
        for c in cats:
            prefix = "✅ " if c in user.interests else ""
            builder.button(
                text=f"{prefix}{c.name}",
                callback_data=f"toggleinterest_{user.id}_{c.id}"
            )
        builder.button(text="◀️ Назад", callback_data="user_profile")
        builder.adjust(2)

        await callback.message.edit_text(
            "Выберите свои интересы (кликните, чтобы переключить)\n"
            "✅ — помечены подписки, на которые вы уже подписаны:",
            reply_markup=builder.as_markup()
        )
    finally:
        db.close()
    await callback.answer()


@user_profile_router.callback_query(F.data.startswith("toggleinterest_"))
async def toggle_interest(callback: types.CallbackQuery):
    # Разбираем callback_data
    _, user_id_str, cat_id_str = callback.data.split("_", 2)
    user_id, cat_id = int(user_id_str), int(cat_id_str)

    db = next(get_db())
    try:
        # Подгружаем user вместе с interests
        user = (
            db.query(User)
              .options(joinedload(User.interests))
              .filter(User.id == user_id)
              .first()
        )
        category = db.query(Category).filter(Category.id == cat_id).first()

        if not user or not category:
            return await callback.answer("Пользователь или категория не найдены", show_alert=True)

        # toggle
        if category in user.interests:
            user.interests.remove(category)
        else:
            user.interests.append(category)

        db.commit()

        db.refresh(user)

        # Перестраиваем клавиатуру
        cats = db.query(Category).order_by(Category.name).all()
        builder = InlineKeyboardBuilder()
        for c in cats:
            prefix = "✅ " if c in user.interests else ""
            builder.button(
                text=f"{prefix}{c.name}",
                callback_data=f"toggleinterest_{user.id}_{c.id}"
            )
        builder.button(text="◀️ Назад", callback_data="user_profile")
        builder.adjust(2)

        await callback.answer("🔄 Интерес обновлён")
    except Exception as e:
        logging.exception("Ошибка при toggle_interest")
        # plain-text, без HTML
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
    finally:
        db.close()

USERS_PER_PAGE = 10


@user_profile_router.callback_query(F.data == "edit_user_interests")
async def cmd_edit_interests(callback: types.CallbackQuery):
    """
    Старт: админ вводит команду, получает первую страницу пользователей.
    """
    try:
        db = next(get_db())
        users = db.query(User).order_by(User.username).all()
        db.close()

        # Подготавливаем «сырые» данные для пагинатора:
        # можно передавать dict или InlineKeyboardButton напрямую
        data = [
            {"text": u.username or f"{u.first_name} {u.last_name}", "callback_data": f"edit_uinterest_{u.id}"}
            for u in users
        ]

        paginator = KeyboardPaginator(
            data,  # data
            user_profile_router,  # router
            [],  # additional_buttons
            ["⏪", "⬅️", "➡️", "⏩"],  # pagination_buttons
            USERS_PER_PAGE,
            (1,1)
        )

        # Шлём первую страницу
        await callback.message.answer(
            "👥 Выберите пользователя для редактирования интересов:",
            reply_markup=paginator.as_markup()
        )

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")


@user_profile_router.callback_query(F.data.startswith("edit_uinterest_"))
async def edit_user(callback: CallbackQuery):
    try:
        # Правильное извлечение ID
        user_id = int(callback.data[len("edit_uinterest_"):])

        db = next(get_db())
        user = db.query(User).options(joinedload(User.interests)).filter(User.id == user_id).first()
        if not user:
            # Если вдруг пользователь удалён или ID неверен
            await callback.answer("❗ Пользователь не найден", show_alert=True)
            db.close()
            return
        categories = db.query(Category).order_by(Category.name).all()
        db.close()

        builder = InlineKeyboardBuilder()
        for cat in categories:
            subscribed = cat in user.interests
            builder.button(
                text=f"{'✅' if subscribed else '☑️'} {cat.name}",
                callback_data=f"catchinterest_{user_id}_{cat.id}"
            )
        builder.button(text="🔙 Назад", callback_data="back_to_user_list")
        builder.adjust(2)

        await callback.message.edit_text(
            f"✍️ Редактируем интересы <b>{user.username or user.first_name}</b>:",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при загрузке категорий: {e}")
        await callback.answer()


@user_profile_router.callback_query(F.data == "back_to_user_list")
async def back_to_list(callback: CallbackQuery):
    """
    Возврат к списку пользователей — просто повторяем старт /edit_interests.
    """
    # вызывает тот же код, что на /edit_interests
    await cmd_edit_interests(callback)
    await callback.answer()


@user_profile_router.callback_query(F.data.startswith("catchinterest_"))
async def toggle_interest(callback: CallbackQuery):
    db = next(get_db())
    try:
        _, user_id_str, cat_id_str = callback.data.split("_")
        user_id, cat_id = int(user_id_str), int(cat_id_str)

        user = (
            db.query(User)
              .options(joinedload(User.interests))
              .filter(User.id == user_id)
              .first()
        )
        category = db.query(Category).get(cat_id)

        if not user or not category:
            return await callback.answer("❌ Пользователь или категория не найдены", show_alert=True)

        if category in user.interests:
            user.interests.remove(category)
        else:
            user.interests.append(category)

        db.commit()

        # теперь безопасно строим клавиатуру, session всё ещё жива
        categories = db.query(Category).order_by(Category.name).all()

        builder = InlineKeyboardBuilder()
        for cat in categories:
            subscribed = cat in user.interests   # session открыта, lazy load работает
            builder.button(
                text=f"{'✅' if subscribed else '☑️'} {cat.name}",
                callback_data=f"catchinterest_{user_id}_{cat.id}"
            )
        builder.button(text="🔙 Назад", callback_data="back_to_user_list")
        builder.adjust(2)

        await callback.answer("🔄 Интерес обновлён")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка",)
        logging.info(f"❌ Ошибка: {e}")
        await callback.answer()
    finally:
        db.close()
