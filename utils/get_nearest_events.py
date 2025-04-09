import logging
from datetime import datetime
from db.database import get_db, Event


async def get_nearest_event():
    """
    Возвращает ближайшее по дате событие (с event_time >= текущего времени)
    или None, если таких событий нет.
    """
    db = next(get_db())
    try:
        now = datetime.utcnow()
        # Получаем ближайшее предстоящее событие (по возрастанию времени)
        event = (
            db.query(Event)
            .filter(Event.event_time >= now)
            .order_by(Event.event_time.asc())
            .first()
        )
        return event
    except Exception as e:
        logging.exception(f"Ошибка при получении ближайшего события: {e}")
        return None
    finally:
        db.close()