import random
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot
from db.database import get_db, Registration, Event, User
from datetime import datetime
load_dotenv()

CHAT_ID = os.getenv("CHAT_ID")


async def divide_teams_for_current_event(bot: Bot):
    """
    Делит участников текущего (активного) события на две команды сразу после начала матча
    и отправляет сообщение в чат с красивым оформлением и эмодзи.
    Функция автоматически выбирает событие, для которого event_time <= now и is_checked == False.
    После разделения устанавливается is_checked=True, чтобы избежать повторной обработки.
    """
    db = next(get_db())
    try:
        now = datetime.utcnow()
        # Выбираем последнее событие, которое уже началось и еще не было обработано
        event = (
            db.query(Event)
            .filter(Event.event_time <= now, Event.is_team_divide == False)
            .order_by(Event.event_time.desc())
            .first()
        )
        if not event:
            await bot.send_message(chat_id=CHAT_ID, text="Нет активного события для разделения команд.")
            return

        registrations = db.query(Registration).filter_by(event_id=event.id).all()
        players = [reg.user for reg in registrations if reg.user is not None]
        if not players:
            await bot.send_message(chat_id=CHAT_ID, text="Нет участников для разделения команд.")
            return

        # Перемешиваем игроков случайным образом
        random.shuffle(players)
        n = len(players)
        mid = n // 2
        team1 = players[:mid]
        team2 = players[mid:]

        # Формируем списки участников с эмодзи
        team1_text = "\n".join([f"⚡️ {p.first_name} {p.last_name or ''}".strip() for p in team1])
        team2_text = "\n".join([f"🔥 {p.first_name} {p.last_name or ''}".strip() for p in team2])

        message_text = (
            f"🏐 <b>Разделение команд для матча «{event.name}»</b> 🏐\n\n"
            f"💪 <b>Команда 1</b> ({len(team1)} участников):\n{team1_text}\n\n"
            f"🤩 <b>Команда 2</b> ({len(team2)} участников):\n{team2_text}\n\n"
            f"Желаем удачи и отличной игры! 🎉"
        )

        await bot.send_message(chat_id=CHAT_ID, text=message_text)

        # Помечаем событие, как обработанное, чтобы не делить его повторно
        event.is_team_divide = True
        db.commit()
    except Exception as e:
        logging.exception("Ошибка при разделении команд для текущего события: %s", e)
    finally:
        db.close()