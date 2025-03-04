import logging
import random
import json
import urllib.parse
import os
from aiogram import types, Router, Bot, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ContentType, InlineQueryResultArticle, \
    InputTextMessageContent, KeyboardButton, ReplyKeyboardMarkup
from db.database import get_db, User, Event, Registration
from datetime import datetime, timedelta
from dotenv import load_dotenv

from utils.get_random_users import get_three_random_users

load_dotenv()

NG_ROCK_URL = os.getenv("NG_ROCK_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

mvp_pool_router = Router()


@mvp_pool_router.callback_query(F.data == "parse_users")
async def show_users_mini_app(callback: types.CallbackQuery):
    users_data = get_three_random_users()

    data_json = json.dumps({"users": users_data})
    encoded_data = urllib.parse.quote(data_json)

    # Формируем URL мини‑приложения с параметром data
    # Замените YOUR_NGROK_URL на актуальный публичный адрес (например, полученный через ngrok)
    mini_app_url = f"{NG_ROCK_URL}/index.html?data={encoded_data}"

    # Создаём inline-клавиатуру с кнопкой, которая открывает мини‑приложение
    keyboard = ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text="Открыть мини‑приложение", web_app=WebAppInfo(url=mini_app_url))
    ]], resize_keyboard=True, one_time_keyboard=True)

    await callback.message.answer("Нажмите кнопку для открытия мини‑приложения:", reply_markup=keyboard)


@mvp_pool_router.message(lambda message: message.content_type == "web_app_data")
async def handle_webapp_data(message: types.Message):
    data_str = message.web_app_data.data
    try:
        data = json.loads(data_str)
        await message.answer(f"Вы проголосовали за {data['first_name']} {data['last_name']}")
    except Exception as e:
        await message.answer(f"Ошибка при разборе данных: {e}")