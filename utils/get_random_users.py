import random
import logging
from sqlalchemy.exc import SQLAlchemyError
from db.database import get_db, User, Event, Registration


def get_three_random_users(event_id):
    db = next(get_db())
    try:
        registrations = db.query(Registration).filter_by(event_id=event_id).all()
        if len(registrations) < 3:
            logging.warning("Недостаточно записей для выбора 3 случайных пользователей")
            return []  # или можно вернуть registrations, если их меньше трёх
        selected_regs = random.sample(registrations, 3)
        users_data = [{
            "id": reg.user.id,
            "first_name": reg.user.first_name,
            "last_name": reg.user.last_name,
            "photo_file_id": reg.user.photo_file_id
        } for reg in selected_regs]
        return users_data
    except SQLAlchemyError as e:
        logging.info(f"Ошибка при получении данных: {e}")
        return []
