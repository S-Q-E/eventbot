from datetime import datetime
from db.database import Event, get_db
import logging


def get_active_events():
    """
    Получает ID всех событий, которые уже начались.
    Returns:
        list[int]: Список ID начавшихся событий.
    """
    db = next(get_db())
    try:
        now = datetime.utcnow()
        active_events = db.query(Event).filter(Event.event_time <= now).all()

        if not active_events:
            logging.info("Нет активных событий")
            return []

        return [event.id for event in active_events]
    except Exception as e:
        logging.error(f"Ошибка при получении активных событий: {e}")
        return []
    finally:
        db.close()