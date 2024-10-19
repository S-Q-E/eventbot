from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_router = Router()


@start_router.message(Command("start"))
async def start_command(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """
    # Создаем кнопки
    create_event = InlineKeyboardButton(text="Создать событие", callback_data="create_event")
    events_button = InlineKeyboardButton(text="События", callback_data="events")
    my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")

    # Передаем кнопки в виде списка списков (каждая строка клавиатуры - отдельный список)
    markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button], [create_event]])

    await message.answer("Привет! Выберите опцию:", reply_markup=markup)
