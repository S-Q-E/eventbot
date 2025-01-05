from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.database import get_db, Event
from utils.feedback_request import send_feedback_request
from utils.notify_user import send_notifications
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()


def check_events(bot: Bot, db_session: get_db):
    """
    Планирует отправку уведомлений для всех событий.

    Args:
        bot: Экземпляр бота Telegram.
        db_session: Сессия базы данных.
    """
    with db_session as db:
        events = db.query(Event).filter(Event.event_time >= datetime.now()).all()
        for event in events:
            # Если событие уже есть в планировщике, пропустим его
            job_id = f"notify_event_{event.id}"
            if scheduler.get_job(job_id):
                continue

            scheduler.add_job(
                send_feedback_request,
                trigger="date",
                run_date=event.event_time + timedelta(minutes=120),
                args=[bot, event.id, event.name],
                id=job_id
            )


# async def check_events(bot: Bot):
#     """
#     Проверяет начавшиеся события и вызывает обработчик для каждого.
#     """
#     with next(get_db()) as db:
#         try:
#             started_events = get_started_events(db)
#             for event in started_events:
#                 await send_feedback_request(bot, event["id"], event["name"])
#         except Exception as e:
#             print(f"Ошибка при проверке событий: {e}")
#         finally:
#             db.close()


def start_scheduler(bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(send_notifications, 'interval', minutes=1, args=[bot])
    scheduler.add_job(check_events, "interval", seconds=60, args=[bot, next(get_db())])  # Интервал: 1 минута
    scheduler.start()
