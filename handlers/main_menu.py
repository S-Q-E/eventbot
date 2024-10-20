from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_menu_router = Router()


@main_menu_router.message(Command("main_menu"))
async def start_command(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """

    create_event = InlineKeyboardButton(text="Создать событие", callback_data="create_event")
    events_button = InlineKeyboardButton(text="События", callback_data="events")
    my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")

    markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button], [create_event]])

    await message.answer("Привет! Выберите опцию:", reply_markup=markup)

