from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.notify_user import send_notifications
from utils.send_mvp_pool import send_mvp_links

scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(send_notifications, 'interval', minutes=1, args=[bot])
    scheduler.add_job(send_mvp_links, 'interval', minutes=1, args=[bot])
    scheduler.start()
