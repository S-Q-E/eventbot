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
            logging.info(f"Опрос {poll.id} не найден в активных сессиях")
            return

        # Получаем всех кандидатов
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        if not candidates:
            logging.info("Нет кандидатов для обновления голосов")
            return

        logging.info(f"Обновляем голоса для опроса {poll.id}")
        logging.info(f"Количество кандидатов: {len(candidates)}")
        logging.info(f"Количество опций в опросе: {len(poll.options)}")

        # Сопоставляем опции опроса с кандидатами по ID
        for i, option in enumerate(poll.options):
            logging.info(f"Обрабатываем опцию {i}: {option.text} с {option.voter_count} голосами")
            
            # Извлекаем ID кандидата из текста опции
            if "(ID:" in option.text:
                try:
                    # Ищем ID в формате "(ID:123)"
                    id_start = option.text.find("(ID:") + 4
                    id_end = option.text.find(")", id_start)
                    candidate_id = int(option.text[id_start:id_end])
                    
                    # Находим кандидата по ID
                    candidate = next((c for c in candidates if c.id == candidate_id), None)
                    if candidate:
                        old_votes = candidate.votes
                        candidate.votes = option.voter_count
                        logging.info(f"Обновлен кандидат {candidate.first_name} {candidate.last_name}: {old_votes} -> {candidate.votes}")
                    else:
                        logging.warning(f"Кандидат с ID {candidate_id} не найден в базе данных")
                        
                except (ValueError, IndexError) as e:
                    logging.error(f"Ошибка при извлечении ID из опции '{option.text}': {e}")
            else:
                logging.warning(f"Опция '{option.text}' не содержит ID кандидата")

        db.commit()
        logging.info("Голоса успешно обновлены")

    except Exception as e:
        logging.error(f"Ошибка при обновлении результатов опроса: {e}")
        db.rollback()
    finally:
        db.close()

