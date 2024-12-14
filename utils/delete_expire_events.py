import os
from dotenv import load_dotenv
from aiogram import Bot
from db.database import get_db, Event
from datetime import datetime
import logging

load_dotenv()
ADMIN = os.getenv("ADMIN_2")


async def delete_expired_events(bot: Bot):
    """
    Удаляет события, дата и время которых уже прошли.
    """
    try:
        db = next(get_db())
        now = datetime.now()
        expired_events = db.query(Event).filter(Event.event_time < now).all()

        if not expired_events:
            logging.info("Нет истекших событий для удаления.")
            return

        deleted_events_list = "\n".join(f"⚠️ Событие <b>{event.name}</b> (ID: {event.id}) завершилось и будет удалено."
                                        for event in expired_events)

        await bot.send_message(int(ADMIN), deleted_events_list)

        for event in expired_events:
            db.delete(event)
            db.commit()

            logging.info(f"Удалено событий: {len(expired_events)} \n")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления админу {ADMIN}: {e}")
        logging.error(f"Ошибка при удалении истекших событий: {e}")
