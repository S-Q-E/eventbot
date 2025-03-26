from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.get_random_users import check_and_process_events
from utils.notify_user import send_notifications
from utils.send_pool import send_mvp_poll, finish_mvp_poll

scheduler = AsyncIOScheduler()


def start_scheduler(bot: Bot):
    """
    Запускает планировщик задач.
    """
    scheduler.add_job(check_and_process_events, 'interval', minutes=1)
    scheduler.add_job(send_mvp_poll, "cron", day_of_week="sun", hour=22, args=[bot])
    scheduler.add_job(finish_mvp_poll, 'cron', day_of_week="mon", hour=16, minute=19, args=[bot])
    scheduler.start()
