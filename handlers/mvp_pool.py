from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User, Event

mvp_pool_router = Router()

@mvp_pool_router.callback_query("choose_random")
async def choose_random_user(callback: types.CallbackQuery):
    try:
        db = get_db()
