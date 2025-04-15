import logging
from sched import scheduler

from aiogram import types, Router, F
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
    events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_page_1")
    registration_button = InlineKeyboardButton(text="➕ Регистрация", callback_data="start_reg")

    try:
        user = db.query(User).filter_by(id=user_id).first()
    except Exception as e:
        await message.answer("Произошла ошибка при доступе к базе данных. Попробуйте позже.")
        logging.info(f"Ошибка в start_command.py {e}")

        return

    if not user:
        markup = InlineKeyboardMarkup(inline_keyboard=[[registration_button], [events_button]])
        try:
            new_user = User(id=user_id, username=message.from_user.username)
            db.add(new_user)
            db.commit()
            await message.answer("Пройдите регистрацию для получения всех возможностей бота.", reply_markup=markup)
        except Exception as e:
            await message.answer(f"Произошла ошибка при регистрации. Попробуйте снова.\n"
                                 f"Ошибка{e}")
        else:
            await message.answer("Вы не завершили регистрацию. Пожалуйста, пройдите её.", reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [registration_button]])
        await message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                             f"Добро пожаловать! <b>{message.from_user.username}</b>", reply_markup=markup)


@start_router.message(F.photo)
async def handle_message(message: types.Message):
    if message.document:
        await message.reply(f"Document file_id: {message.document.file_id}")
    elif message.photo:
        # берем фото с наивысшим разрешением
        await message.reply(f"Photo file_id: {message.photo[-1].file_id}")
    else:
        await message.reply("Нет файла для получения file_id")
