from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

from utils.devide_team import divide_teams_for_current_event
from utils.mvp_poll import get_started_events, start_voting, end_voting

scheduler = AsyncIOScheduler()

async def run_sync_in_thread(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)

async def start_scheduler(bot: Bot):
    # Запускаем синхронные функции в отдельных потоках, чтобы не блокировать event loop
    scheduler.add_job(lambda: asyncio.create_task(run_sync_in_thread(get_started_events)), 'interval', hours=12)
    scheduler.add_job(start_voting, 'cron', day_of_week='sun', hour=22, minute=0, args=[bot])
    scheduler.add_job(end_voting, 'cron', day_of_week='mon', hour=12, minute=0, args=[bot])
    scheduler.add_job(divide_teams_for_current_event, 'interval', minutes=1, args=[bot])
    scheduler.start()
