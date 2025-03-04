import json
import urllib.parse
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from db.database import get_db, Event, Registration, User
from utils.get_random_users import get_three_random_users

load_dotenv()

NGROK_URL = os.getenv("NG_ROCK_URL")


def build_mini_app_url(event_id, users_data):
    data_json = json.dumps({"users": users_data})
    encoded_data = urllib.parse.quote(data_json)
    return f"{NGROK_URL}/index.html?data={encoded_data}"


async def send_mvp_links(bot: Bot):
    db = next(get_db())
    now = datetime.now()
    events = db.query(Event).filter(Event.event_time <= now - timedelta(hours=2)).all()
    for event in events:
        if not event.is_mvp_sent:
            registrations = db.query(Registration).filter(Registration.event_id == event.id).all()

            users_data = get_three_random_users(event.id)
            if not users_data:
                logging.warning("Недостаточно участников для события %s", event.id)
                continue
            mini_app_url = build_mini_app_url(event.id, users_data)
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Открыть мини‑приложение", web_app=WebAppInfo(url=mini_app_url))]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            for reg in registrations:
                try:
                    await bot.send_message(
                        chat_id=reg.user.id,
                        text=f"Прошло 2 часа с начала матча <b>{event.name}</b>! Пройдите опрос за MVP.",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logging.error("Не удалось отправить ссылку пользователю %s: %s", reg.user_id, e)
            event.is_mvp_sent = True
            db.commit()
    db.close()
