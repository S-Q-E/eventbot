from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.prepare_poll import get_started_events

scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(get_started_events, 'interval', minutes=5)
    scheduler.start()

