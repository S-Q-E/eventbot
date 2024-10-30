from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# from utils.reg_required import registration_required

main_menu_router = Router()


# @registration_required
@main_menu_router.message(Command("main_menu"))
@main_menu_router.callback_query(F.data == "main_menu")
async def main_menu(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """

    create_event = InlineKeyboardButton(text="Создать событие", callback_data="create_event")
    events_button = InlineKeyboardButton(text="События", callback_data="events")
    my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")

    markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button], [create_event]])

    await message.answer("*******EVENTBOT********\n\n"
                         f"<b>Добро пожаловать! {message.from_user.username}</b>\n", reply_markup=markup)
