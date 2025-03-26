from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.start()
