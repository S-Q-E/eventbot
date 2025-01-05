import logging

from aiogram import Bot
from db.database import get_db, Registration, Event
from datetime import datetime, timedelta


async def send_notifications(bot: Bot):
    reminder_time = ""
    db = next(get_db())
    try:
        now = datetime.now()

        # Получаем все регистрации с уведомлениями
        registrations = db.query(Registration).filter(Registration.reminder_time.isnot(None)).all()

        for reg in registrations:
            event = db.query(Event).filter_by(id=reg.event_id).first()
            if not event:
                continue

            # Вычисляем время уведомления
            notify_time = event.event_time
            if reg.reminder_time == '24h':
                reminder_time = "сутки"
                notify_time -= timedelta(hours=24)
            elif reg.reminder_time == '2h':
                reminder_time = "2 часа"
                notify_time -= timedelta(hours=2)

            # Проверяем, нужно ли отправить уведомление сейчас
            if notify_time <= now < (notify_time + timedelta(minutes=5)):
                await bot.send_message(
                    reg.user_id,
                    f"Напоминание! Событие {event.name} начнется через {reminder_time}."
                )
                reg.reminder_time = None
                db.commit()
    except Exception as e:
        logging.info(f"Ошибка в {__name__} {e}")
    finally:
        db.close()

