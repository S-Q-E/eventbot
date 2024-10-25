import logging
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User


logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
        "[%(asctime)s] - %(name)s - %(message)s",
    )

start_router = Router()


@start_router.message(Command("start"))
async def start_command(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """
    db = next(get_db())

    # Проверка пользователя
    user_id = message.from_user.id

    # Кнопки
    create_event = InlineKeyboardButton(text="Создать событие", callback_data="create_event")
    events_button = InlineKeyboardButton(text="События", callback_data="events")
    my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")
    registration_button = InlineKeyboardButton(text="Регистрация", callback_data="start_reg")

    try:
        user = db.query(User).filter_by(id=user_id).first()
    except Exception as e:
        await message.answer("Произошла ошибка при доступе к базе данных. Попробуйте позже.")

        return

    if not user:
        markup = InlineKeyboardMarkup(inline_keyboard=[[registration_button], [events_button]])
        try:
            new_user = User(id=user_id, username=message.from_user.username, is_registered=False)
            db.add(new_user)
            db.commit()
            await message.answer("Пройдите регистрацию для получения всех возможностей бота.", reply_markup=markup)
        except Exception as e:
            await message.answer(f"Произошла ошибка при регистрации. Попробуйте снова.\n"
                                 f"Ошибка{e}")
        else:
            await message.answer("Вы не завершили регистрацию. Пожалуйста, пройдите её.", reply_markup=markup)
    else:
        if user.is_registered:
            markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button], [create_event]])
            await message.answer(f"Добро пожаловать, {user.first_name}! Вы зарегистрированы.", reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup(inline_keyboard=[[registration_button], [events_button]])
            await message.answer(f"Проидите регистрацию", reply_markup=markup)
