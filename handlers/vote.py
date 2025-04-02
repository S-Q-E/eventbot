import logging
import os
from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.database import User, Event, Registration, get_db, VotingSession
from utils.mvp_poll import announce_winner

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")

vote_router = Router()


@vote_router.poll()
async def handle_poll(poll: types.Poll):
    db = next(get_db())
    try:
        # Получение последнего активного голосования
        voting_session = db.query(VotingSession).order_by(VotingSession.id.desc()).first()
        if not voting_session or voting_session.poll_id != poll.id:
            return

        # Обновление количества голосов для каждого кандидата
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        for i, option in enumerate(poll.options):
            if i < len(candidates):
                candidates[i].votes = option.voter_count
        db.commit()

    except Exception as e:
        logging.error(f"Ошибка при обновлении результатов опроса: {e}")
        db.rollback()
    finally:
        db.close()

