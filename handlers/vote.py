import logging
import os
from aiogram import types, Router, F
from db.database import User, get_db, VotingSession
from dotenv import load_dotenv


load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")

vote_router = Router()

@vote_router.poll()
async def handle_poll(poll: types.Poll):
    with get_db() as db:
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

            # Сопоставляем опции опроса с кандидатами по ID
            for option in poll.options:
                # Извлекаем ID кандидата из текста опции (формат: "Имя (ID:123)")
                if "(ID:" in option.text:
                    try:
                        id_start = option.text.find("(ID:") + 4
                        id_end = option.text.find(")", id_start)
                        candidate_id = int(option.text[id_start:id_end])
                        
                        candidate = next((c for c in candidates if c.id == candidate_id), None)
                        if candidate:
                            candidate.votes = option.voter_count
                    except (ValueError, IndexError):
                        continue

            db.commit()
            logging.info("Голоса успешно обновлены")
        except Exception as e:
            logging.error(f"Ошибка при обновлении результатов опроса: {e}")
