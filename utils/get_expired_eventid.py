from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.database import Registration, User, Event


def get_users_for_feedback(db: Session, event_id: int):
    """
    Получает список пользователей, которым нужно отправить запрос на отзыв.

    Args:
        db: Объект сессии базы данных SQLAlchemy.
        event_id: ID события.

    Returns:
        Список пользователей, которым нужно отправить запрос.
    """
    registrations = (
        db.query(Registration)
        .filter(
            Registration.event_id == event_id,
            Registration.has_given_feedback == False  # Только пользователи без отзыва
        )
        .join(User, Registration.user_id == User.id)
        .all()
    )
    return [reg.user for reg in registrations]


def get_started_events(db: Session):
    """
    Проверяет, есть ли начавшиеся события.

    Args:
        db: Объект сессии базы данных SQLAlchemy.

    Returns:
        Список словарей с id и именем начавшихся событий.
    """
    request_time = datetime.now() + timedelta(minutes=1)
    events = db.query(Event).filter(Event.event_time <= request_time).all()
    started_events = [{"id": event.id, "name": event.name} for event in events]
    return started_events


