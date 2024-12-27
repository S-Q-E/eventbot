import os
from dotenv import load_dotenv
from aiogram import Bot
from db.database import get_db, Event, Registration, User
from datetime import datetime, timedelta
import logging
import pandas as pd

from utils.feedback_request import send_feedback_request

load_dotenv()
ADMIN = os.getenv("ADMIN_2")


async def delete_expired_events(bot: Bot):
    """
    Экспортирует истекшие события и регистрации в Excel, затем удаляет данные из базы.
    """
    try:
        db = next(get_db())
        now = datetime.now()
        expired_events = db.query(Event).filter(Event.event_time + timedelta(minutes=12) < now).all()

        if not expired_events:
            logging.info("Нет истекших событий для удаления.")
            return

        export_data = []
        for event in expired_events:
            registrations = db.query(Registration).filter(Registration.event_id == event.id).all()
            for reg in registrations:
                await send_feedback_request(bot=bot, event_id=event.id,event_name=event.name)
                user = db.query(User).filter(User.id == reg.user_id).first()
                export_data.append({
                    "Event Name": event.name,
                    "Event ID": event.id,
                    "Event DateTime": event.event_time.strftime("%Y-%m-%d %H:%M"),
                    "User ID": user.id if user else "Unknown",
                    "User Name": f"{user.first_name} {user.last_name}" if user else "Unknown",
                    "User Phone": user.phone_number if user else "Unknown",
                })

        # Экспорт данных в Excel
        if export_data:
            df = pd.DataFrame(export_data)
            filename = f"expired_events_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join("exports", filename)
            os.makedirs("exports", exist_ok=True)
            df.to_excel(filepath, index=False)
            await bot.send_message(int(ADMIN), f"Данные об истекших событиях сохранены в файл: {filename}")

        deleted_events_list = "\n".join(
            f"⚠️ Событие <b>{event.name}</b> (ID: {event.id}) завершилось и будет удалено."
            for event in expired_events
        )
        await bot.send_message(int(ADMIN), deleted_events_list)

        for event in expired_events:
            db.query(Registration).filter(Registration.event_id == event.id).delete()
            db.delete(event)
        db.commit()

        logging.info(f"Удалено событий: {len(expired_events)}. Данные сохранены в папку exports.")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления админу {ADMIN}: {e}")
        logging.error(f"Ошибка при удалении истекших событий: {e}")
