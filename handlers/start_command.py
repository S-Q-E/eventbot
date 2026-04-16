import logging
import html
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
    with get_db() as db:
        # Проверка пользователя
        user_id = message.from_user.id

        # Кнопки
        events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
        registration_button = InlineKeyboardButton(text="➕ Регистрация", callback_data="start_reg")

        try:
            user = db.query(User).filter_by(id=user_id).first()
        except Exception as e:
            await message.answer("Произошла ошибка при доступе к базе данных. Попробуйте позже.")
            logging.info(f"Ошибка в start_command.py {e}")

            return

        safe_username = html.escape(message.from_user.username or message.from_user.first_name or "Пользователь")

        if not user:
            markup = InlineKeyboardMarkup(inline_keyboard=[[registration_button], [events_button]])
            try:
                new_user = User(id=user_id, username=message.from_user.username)
                db.add(new_user)
                await message.answer(f"Привет, <b>{safe_username}!</b>\n\n"
                                     f"✅ Это приложение для участников спортивных событий\n"
                                     f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время", reply_markup=markup)
            except Exception as e:
                await message.answer(f"Произошла ошибка при регистрации. Попробуйте снова.\n"
                                     f"Ошибка{e}")
        else:
            markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [registration_button]])
            await message.answer(f"Привет, <b>{safe_username}!</b>\n\n"
                                 f"✅ Это приложение для участников спортивных событий\n"
                                 f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n\n"
                                 , reply_markup=markup)
