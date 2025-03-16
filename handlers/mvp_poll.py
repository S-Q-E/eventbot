import logging
import os
from aiogram import Router, types, F
from sqlalchemy.exc import SQLAlchemyError

from db.database import get_db, MVPCandidate
from utils.send_pool import send_mvp_poll, process_mvp_results
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

GROUP_CHAT_ID = os.getenv("CHAT_ID")

mvp_router = Router()


@mvp_router.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    """Обрабатывает результаты голосования."""
    try:
        with next(get_db()) as db:
            poll_id = poll_answer.poll_id
            voter_id = poll_answer.user.id
            selected_option_index = poll_answer.option_ids[0]

            candidates = (
                db.query(MVPCandidate)
                .filter(MVPCandidate.is_selected == True)
                .order_by(MVPCandidate.id.desc())
                .limit(3)
                .all()
            )

            if len(candidates) < 3:
                logging.warning("Ошибка: количество кандидатов в базе меньше 3")

            selected_candidate = candidates[selected_option_index]
            selected_candidate.votes += 1

            db.commit()
            logging.info(f"Голос от {voter_id} засчитан за {selected_candidate.user_id} poll_id:{poll_id}")
    except SQLAlchemyError as e:
        logging.info(f"Ошибка в {__name__} {e}")
        db.rollback()
    except IndexError as e:
        logging.info("Ошибка индекса: Пользователь выбрал неверный вариант ответа")
    except Exception as e:
        logging.info(f"Нейзвестная ошибка {e}")
    finally:
        db.close()

