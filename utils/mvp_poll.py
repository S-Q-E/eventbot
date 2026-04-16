import random
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from db.database import get_db, Event, Registration, User, VotingSession
from datetime import datetime

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")
ADMIN = os.getenv("ADMIN_2")
DEFAULT_PHOTO = os.getenv("DEFAULT_PHOTO_ID")


def get_started_events():
    with get_db() as db:
        try:
            now = datetime.now()
            events = db.query(Event).filter(
                Event.event_time < now,
                Event.is_checked == False,
                Event.category_id == 2
            ).all()
            for event in events:
                candidate = choose_mvp_candidate(event.id)
                if candidate:
                    logging.info(f"Выбран MVP-кандидат для события {event.id}: {candidate.id}")
                event.is_checked = True
            db.commit()
        except Exception as e:
            logging.error(f"Ошибка в get_started_events: {e}")


def choose_mvp_candidate(event_id: int):
    with get_db() as db:
        try:
            registrations = db.query(Registration).filter(
                Registration.event_id == event_id,
                Registration.user.has(User.is_mvp_candidate == False)
            ).all()
            if not registrations:
                return None

            selected_registration = random.choice(registrations)
            selected_registration.user.is_mvp_candidate = True
            db.commit()
            return selected_registration.user
        except Exception as e:
            logging.error(f"Ошибка в choose_mvp_candidate: {e}")
            return None


def announce_winner():
    with get_db() as db:
        try:
            candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
            if not candidates:
                return None, None

            winner = max(candidates, key=lambda user: user.votes)
            winner_photo_id = winner.photo_file_id if winner.photo_file_id else DEFAULT_PHOTO
            winner_name = f"{winner.first_name} {winner.last_name}"
            
            db.query(User).filter(User.is_mvp_candidate == True).update({User.is_mvp_candidate: False})
            db.query(User).update({User.votes: 0})
            db.commit()
            
            return winner_name, winner_photo_id
        except Exception as e:
            logging.error(f"Ошибка в announce_winner: {e}")
            return None, None


async def start_voting(bot: Bot):
    logging.info("Начинается голосование!")
    with get_db() as db:
        try:
            candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
            if not candidates:
                await bot.send_message(chat_id=ADMIN, text="Нет кандидатов на голосование")
                return
            
            media = []
            options = []
            for candidate in candidates:
                display_name = f"🏆 {candidate.first_name} {candidate.last_name}"
                photo = candidate.photo_file_id if candidate.photo_file_id else DEFAULT_PHOTO
                media.append(InputMediaPhoto(media=photo, caption=display_name))
                options.append(f"{candidate.first_name} {candidate.last_name} (ID:{candidate.id})")
            
            await bot.send_media_group(chat_id=CHAT_ID, media=media)
            poll_message = await bot.send_poll(
                chat_id=CHAT_ID,
                question="Кто лучший игрок?",
                options=options,
                is_anonymous=False
            )
            
            voting_session = VotingSession(poll_id=poll_message.poll.id)
            db.add(voting_session)
            db.commit()
        except Exception as e:
            logging.error(f"Ошибка в start_voting: {e}")


async def end_voting(bot: Bot):
    winner_name, photo_id = announce_winner()
    if winner_name and photo_id:
        await bot.send_photo(chat_id=CHAT_ID,
                             photo=photo_id,
                             caption=f"Звание лучшего игрока недели получает\n 🏆{winner_name} 🏆 \nПоздравляем!🎉")
    else:
        await bot.send_message(chat_id=CHAT_ID, text="Не удалось определить победителя голосования")
