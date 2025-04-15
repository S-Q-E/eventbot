from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.devide_team import divide_teams_for_current_event
from utils.mvp_poll import get_started_events, start_voting, end_voting

scheduler = AsyncIOScheduler()


async def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(get_started_events, 'interval', hours=12)
    scheduler.add_job(start_voting, 'cron', day_of_week='sun', hour=22, minute=00, args=[bot])
    scheduler.add_job(end_voting, 'cron', day_of_week='mon', hour=12, minute=00, args=[bot])
    scheduler.add_job(divide_teams_for_current_event, 'interval', minutes=10, args=[bot])
    scheduler.start()

