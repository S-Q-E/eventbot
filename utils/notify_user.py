import logging

from aiogram import Bot
from db.database import get_db, Registration, Event
from datetime import datetime, timedelta


# Функция для отправки уведомлений
async def send_notifications(bot: Bot):
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
                notify_time -= timedelta(hours=24)
            elif reg.reminder_time == '2h':
                notify_time -= timedelta(hours=2)

            # Проверяем, нужно ли отправить уведомление сейчас
            if notify_time <= now < (notify_time + timedelta(minutes=5)):  # Допуск 1 минута
                await bot.send_message(
                    reg.user_id,
                    f"Напоминание! Событие {event.name} начнется через  {event.event_time.strftime('%d.%m.%Y %H:%M')}."
                )
                # Удаляем напоминание после отправки (если оно одноразовое)
                reg.reminder_time = None
                db.commit()
    except Exception as e:
        logging.info(f"Ошибка в {__name__} {e}")
    finally:
        db.close()

