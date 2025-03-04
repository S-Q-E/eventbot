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

load_dotenv()

NG_ROCK_URL = os.getenv("NG_ROCK_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

mvp_pool_router = Router()

#
# @mvp_pool_router.callback_query(F.data == "choose_random")
# async def choose_random_user(callback: types.CallbackQuery, bot: Bot, event_id: int):
#     db = next(get_db())
#     try:
#         event = db.query(Event).filter_by(id=event_id).first()
#         if not event:
#             logging.error(f"Событие с ID {event_id} не существует")
#             return
#
#         registrations = db.query(Registration).filter(Registration.event_id==event_id).all()
#
#         if len(registrations) < 3:
#             logging.warning("Недостаточно участников для определения MVP матча")
#             return
#
#         selected_registrations = random.sample(registrations, 3)
#         options = [f"{reg.user.first_name} {reg.user.last_name}" for reg in selected_registrations]
#
#     except Exception as e:
#         print("{e}")


@mvp_pool_router.callback_query(F.data == "parse_users")
async def show_users_mini_app(callback: types.CallbackQuery):
    # Получаем всех пользователей из БД
    db = next(get_db())
    users = db.query(User).all()
    db.close()

    users_data = [{
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "photo_file_id": user.photo_file_id
    } for user in users]

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
    print(type(data_str))
    try:
        data = json.loads(data_str)
        print(type(data))
        await message.answer(f"Вы проголосовали за {data['first_name'], data['last_name']} ")
    except Exception as e:
        await message.answer(f"Ошибка при разборе данных: {e}")