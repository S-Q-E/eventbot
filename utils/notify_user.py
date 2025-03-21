import logging
from aiogram import Bot
from db.database import get_db, Registration, Event, User
from datetime import datetime, timedelta


async def send_notifications(bot: Bot):
    reminder_time = ""
    with next(get_db()) as db:
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
                    db.close()
        except Exception as e:
            logging.info(f"Ошибка в {__name__} {e}")
        finally:
            db.close()


async def notify_all_users_event_full(bot: Bot, event: Event):
    db = next(get_db())
    all_users = db.query(User).all()
    text = (
        f"Событие <b>{event.name}</b> ({event.event_time}) теперь полностью укомплектовано! Мест больше нет!"
    )
    for user in all_users:
        try:
            await bot.send_message(chat_id=user.id, text=text)
        except Exception as e:
            logging.error(f"Ошибка при оповещении пользователя {user.id}: {e}")

