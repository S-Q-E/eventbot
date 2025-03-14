import os

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Poll
import logging
from dotenv import load_dotenv
from utils.get_random_users import get_three_random_users, get_event_participants

load_dotenv()

GROUP_CHAT_ID = os.getenv("CHAT_ID")
ADMIN = os.getenv("ADMIN")


async def send_mvp_poll(bot: Bot, event_id: int):
    """Отправляет MediaGroup с 3 фото пользователей и создаёт опрос."""
    users = get_three_random_users(event_id)
    if len(users) < 3:
        await bot.send_message(ADMIN, "Недостаточно участников для голосования за MVP.")
        return

    # Отправляем MediaGroup
    media_group = [InputMediaPhoto(media=user["photo_file_id"], caption=f"{user['first_name']} {user['last_name']}") for user in users]
    await bot.send_media_group(GROUP_CHAT_ID, media=media_group)

    options = [f"{user['first_name']} {user['last_name']}" for user in users]
    poll_message = await bot.send_poll(
        GROUP_CHAT_ID,
        question="Выберите MVP события",
        options=options,
        is_anonymous=False
    )

    return poll_message.message_id, users
