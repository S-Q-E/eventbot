import logging
from db.database import get_db, Registration


def get_user_registration(event_id: int, user_id: int):
    try:
        with next(get_db()) as db:
            registration: Registration = (
            db.query(Registration)
                .filter(
                Registration.event_id == event_id,
                Registration.user_id == user_id
            )
                .first()
            )
            return registration
    except Exception as e:
        logging.info(f"Не удалось найти запись {e}")