from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

event_category_router = Router()


@event_category_router.message(Command("events"))
async def event_categories(message: types.Message):
    # Кнопки категорий
    categories_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Все события", callback_data="show_all_events")],
        [InlineKeyboardButton(text="События на сегодня", callback_data="show_today_events")],
        [InlineKeyboardButton(text="По месяцу", callback_data="show_by_month")],
    ])
    await message.answer("Выберите категорию событий:", reply_markup=categories_markup)
