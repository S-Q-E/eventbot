import random
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.database import get_db, Event, Registration, User
from datetime import datetime


def get_started_events():
    db = next(get_db())
    try:
        event = db.query(Event).all()
        if not event:
            return False
        now = datetime.now()
        events = db.query(Event).filter(
            Event.event_time < now,
            Event.is_checked == False
        ).all()
        for event in events:
            candidate = choose_mvp_candidate(event.id)
            if candidate:
                logging.info(f"Выбран MVP-кандидат для события {event.id}: {candidate.id}")
            else:
                logging.info(f"Не найден кандидат для события {event.id}")

            event.is_checked = True
        db.commit()
    except SQLAlchemyError as e:
        logging.warning(f"Ошибка в get_started_events. {e}")
        db.rollback()
    except Exception as e:
        logging.warning(f"Ошибка в get_started_events. {e}")
        db.rollback()
    finally:
        db.close()


def choose_mvp_candidate(event_id: int):
    """
    Выбирает одного пользователя из регистраций для указанного события, у которого is_mvp_candidate==False.
    Устанавливает флаг is_mvp_candidate=True и возвращает выбранного пользователя.
    """
    db = next(get_db())
    try:
        registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.user.has(User.is_mvp_candidate == False)
        ).all()
        if not registrations:
            logging.info("Нет пользователей для выбора кандидата.")
            return None

        selected_registration = random.choice(registrations)
        selected_registration.user.is_mvp_candidate = True
        db.commit()
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при выборе MVP-кандидата: {e}")
        db.rollback()
    finally:
        db.close()
    return None


def announce_winner():
    """
    Определяет победителя голосования по событию.
    Возвращает пользователя-победителя, а затем сбрасывает флаги is_mvp_candidate и счетчики голосов.
    """
    db: Session = next(get_db())
    try:
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        if not candidates:
            logging.info("Нет кандидатов")
            return None

        winner = max(candidates, key=lambda user: user.votes)
        winner_photo_id = winner.photo_file_id
        winner_name =f"{winner.first_name} {winner.last_name}"
        for candidate in candidates:
            candidate.is_mvp_candidate = False
            candidate.votes = 0
        db.commit()
        return winner_name, winner_photo_id
    except Exception as e:
        logging.info(f"Ошибка в announce winner {e}")
        db.rollback()
    finally:
        db.close()
    return None


