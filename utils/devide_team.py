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
    with get_db() as db:
        try:
            now = datetime.now()
            in_10_min = now + timedelta(minutes=10)

            event = (
                db.query(Event)
                    .filter(Event.event_time > now,
                            Event.event_time <= in_10_min,
                            Event.is_team_divide == False,
                            Event.category_id == 2)
                    .first()
            )

            if not event:
                return

            registrations = db.query(Registration).filter_by(event_id=event.id).all()
            players = [reg.user for reg in registrations if reg.user]

            if len(players) < 8:
                await bot.send_message(chat_id=CHAT_ID, text=f"⚠️ На игру <b>{event.name}</b> недостаточно участников.")
            else:
                random.shuffle(players)
                mid = len(players) // 2
                team1 = players[:mid]
                team2 = players[mid:]
                
                ball_owner = random.choice(players)
                
                t1_names = "\n".join([f"🔹 {p.first_name} {p.last_name}" for p in team1])
                t2_names = "\n".join([f"🔸 {p.first_name} {p.last_name}" for p in team2])
                
                text = (
                    f"⚽️ <b>Игра начинается через 10 минут!</b>\n\n"
                    f"🔵 <b>Команда Синих:</b>\n{t1_names}\n\n"
                    f"⚪️ <b>Команда Белых:</b>\n{t2_names}\n\n"
                    f"🏀 Ответственный за мяч: <b>{ball_owner.first_name} {ball_owner.last_name}</b>"
                )
                await bot.send_message(chat_id=CHAT_ID, text=text)

                for p in players:
                    p.user_games += 1

            event.is_team_divide = True
            db.commit()
        except Exception as e:
            logging.exception(f"Ошибка в divide_teams: {e}")
