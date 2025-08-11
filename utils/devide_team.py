import os
import random
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from db.database import get_db, Registration, Event, User
from dotenv import load_dotenv

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")


async def divide_teams_for_current_event(bot: Bot):
    """
    Делит участников текущего события на команды согласно заданной логике
    и отправляет сообщение в чат с оформлением и эмодзи.
    После разделения помечает событие как обработанное.
    """
    db = next(get_db())
    try:
        now = datetime.now()
        in_10_min = now + timedelta(minutes=10)

        event = (
            db.query(Event)
                .filter(Event.event_time > now,
                        Event.event_time <= in_10_min,
                        Event.is_team_divide == False,
                        Event.category_id == 2)
                .order_by(Event.event_time)
                .first()
        )

        if not event:
            logging.info("Нет событий, начинающихся в ближайшие 10 минут")
            return

        registrations = db.query(Registration).filter_by(event_id=event.id).all()

        players = [reg.user for reg in registrations if reg.user]
        if len(players) < 8:
            await bot.send_message(chat_id=CHAT_ID, text="Недостаточно участников для игры")
            event.is_team_divide = True
            db.commit()
        else:
            random_player = random.choice(players)
            await bot.send_message(
                chat_id=CHAT_ID,
                text=(
                    "Игра начнётся через 10 минут!\n\n"
                    f"Ответственный за мяч: <b>{random_player.first_name} {random_player.last_name}</b>"
                )
            )

            for registration in registrations:
                registration.user.user_games += 1

        event.is_team_divide = True
        db.commit()
    except Exception as e:
        logging.exception("Ошибка при разделении команд для текущего события: %s", e)
    finally:
        db.close()
