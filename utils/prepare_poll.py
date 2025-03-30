import random
import logging
from sqlalchemy.exc import SQLAlchemyError
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
