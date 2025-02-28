from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.notify_user import send_notifications


scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(send_notifications, 'interval', minutes=1, args=[bot])
    # scheduler.add_job(check_events, "interval", seconds=60, args=[bot, next(get_db())])  # Интервал: 1 минута
    scheduler.start()
