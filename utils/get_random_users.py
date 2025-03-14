import random
import logging
from sqlalchemy.exc import SQLAlchemyError
from db.database import get_db, Registration, MVPCandidate


def get_random_user(event_id):
    db = next(get_db())
    try:
        registrations = db.query(Registration).filter_by(event_id=event_id).all()
        if not registrations:
            logging.warning("Нет доступных регистрации")
            return
        selected_reg: Registration = random.choice(registrations)
        new_candidate = MVPCandidate(event_id=event_id,
                                     user_id=selected_reg.user_id,
                                     is_selected=True)
        db.add(new_candidate)
        db.commit()
        return True
    except SQLAlchemyError as e:
        logging.info(f"Ошибка при получении данных: {e}")
        return False
    finally:
        db.close()


def get_event_participants(event_id: int):
    db = next(get_db())
    try:
        registrations = db.query(Registration).filter_by(event_id=event_id).all()
        return [reg.user.id for reg in registrations]
    except SQLAlchemyError as e:
        logging.info(f"Ошибка при доступе к базе данных {__name__} {e}")
        return []
    finally:
        db.close()
