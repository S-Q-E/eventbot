from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



main_menu_router = Router()


@main_menu_router.message()
async def send_main_menu(message: types.Message, callback_data: CallbackData):
    """
    эта функция приветствия. При старте бота прелагается
    выбрать опцию
    :param message:
    :return: None
    """

    markup = InlineKeyboardMarkup()
    events_button = InlineKeyboardButton(text="События", callback_data="events")
    my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")
    markup.add(events_button, my_events_button)
    await message.answer("Привет! Выберите опцию:", reply_markup=markup)

