import os
import random
import logging
from datetime import datetime
from aiogram import Bot
from db.database import get_db, Registration, Event, User
from dotenv import load_dotenv

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")


async def divide_teams_for_current_event(bot: Bot):
    """
    Делит участников текущего (активного) события на команды сразу после начала матча
    и отправляет сообщение в чат с красивым оформлением и эмодзи.
    Если event.max_participants равно 14 – делим на 2 команды,
    если равно 21 – делим на 3 команды.
    После разделения помечаем событие, как обработанное, чтобы не делить его повторно.
    """
    db = next(get_db())
    try:
        now = datetime.utcnow()
        # Выбираем последнее событие, которое уже началось и ещё не разделено на команды
        event = (
            db.query(Event)
                .filter(Event.event_time <= now, Event.is_team_divide == False)
                .order_by(Event.event_time.desc())
                .first()
        )
        if not event:
            logging.info("Нет события для разделения")
            return

        # Определяем число команд по максимальному количеству участников
        if event.max_participants == 14:
            teams_count = 2
            team_emojis = ["💪", "🤩"]
        elif event.max_participants == 21:
            teams_count = 3
            team_emojis = ["💪", "🤩", "🔥"]
        else:
            # Если max_participants отличается – по умолчанию разделяем на 2 команды
            teams_count = 2
            team_emojis = ["💪", "🤩"]

        # Получаем участников события
        registrations = db.query(Registration).filter_by(event_id=event.id).all()
        players = [reg.user for reg in registrations if reg.user is not None]
        if not players:
            await bot.send_message(chat_id=CHAT_ID, text="Нет участников для разделения команд.")
            return

        # Перемешиваем список игроков случайным образом
        random.shuffle(players)
        n = len(players)
        teams = [[] for _ in range(teams_count)]

        base_size = n // teams_count
        remainder = n % teams_count
        start = 0
        for i in range(teams_count):
            extra = 1 if i < remainder else 0
            teams[i] = players[start: start + base_size + extra]
            start += base_size + extra

        teams_text = ""
        for idx, team in enumerate(teams):
            emoji = team_emojis[idx] if idx < len(team_emojis) else ""
            team_names = "\n".join([f"{emoji} {player.first_name} {player.last_name or ''}".strip() for player in team])
            teams_text += f"<b>Команда {idx + 1}</b> ({len(team)} участников):\n{team_names}\n\n"

        message_text = (
            f"🏐 <b>Разделение команд для матча «{event.name}»</b> 🏐\n\n"
            f"{teams_text}"
            f"Желаем удачи и отличной игры! 🎉"
        )

        await bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode="HTML")

        # Помечаем событие, как разделённое, чтобы не повторять операцию
        event.is_team_divide = True
        db.commit()
    except Exception as e:
        logging.exception("Ошибка при разделении команд для текущего события: %s", e)
    finally:
        db.close()
