from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.get_random_users import check_and_process_events
from utils.notify_user import send_notifications
from utils.get_expired_eventid import get_active_events

scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(send_notifications, 'interval', minutes=1, args=[bot])
    scheduler.add_job(check_and_process_events, 'interval', minutes=1)
    scheduler.start()
