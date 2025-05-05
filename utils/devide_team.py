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
                        Event.is_team_divide == False)
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
        event.is_team_divide = True
        db.commit()
        # # Определяем структуру команд в зависимости от количества игроков
        # team_structure = []
        # if total_players == 8:
        #     team_structure = [4, 4]
        # elif total_players == 9:
        #     team_structure = [5, 4]
        # elif total_players == 10:
        #     team_structure = [5, 5]
        # elif total_players == 11:
        #     team_structure = [5, 6]
        # elif total_players == 12:
        #     team_structure = [6, 6]
        # elif total_players == 13:
        #     team_structure = [6, 7]
        # elif total_players == 14:
        #     team_structure = [7, 7]
        # elif total_players == 15:
        #     team_structure = [6, 6, 3]
        # elif total_players == 16:
        #     team_structure = [6, 6, 4]
        # elif total_players == 17:
        #     team_structure = [6, 6, 5]
        # elif total_players == 18:
        #     team_structure = [6, 6, 6]
        # elif total_players == 19:
        #     team_structure = [6, 6, 7]
        # elif total_players == 20:
        #     team_structure = [6, 7, 7]
        # elif total_players == 21:
        #     team_structure = [7, 7, 7]

        # # Разделяем игроков на команды согласно структуре
        # teams = []
        # start_index = 0
        # for size in team_structure:
        #     team = players[start_index:start_index + size]
        #     teams.append(team)
        #     start_index += size
        #
        # # Эмодзи для команд
        # team_emojis = ["💪", "🤩", "🔥"]
        #
        # # Формируем текст сообщения
        # teams_text = ""
        # for idx, team in enumerate(teams):
        #     emoji = team_emojis[idx] if idx < len(team_emojis) else ""
        #     team_names = "\n".join([f"{emoji} {player.first_name} {player.last_name or ''}".strip() for player in team])
        #     teams_text += f"<b>Команда {idx + 1}</b> ({len(team)} участников):\n{team_names}\n\n"
        #
        # message_text = (
        #     f"🏐 <b>Разделение команд для матча «{event.name}»</b> 🏐\n\n"
        #     f"{teams_text}"
        #     f"Желаем удачи и отличной игры! 🎉\n\n"
        #     f"Ответственный за мяч <b>{random_player.user.first_name} {random_player.user.last_name}</b>"
        # )
        #
        # await bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode="HTML")
        #
        # # Помечаем событие как разделенное
        # event.is_team_divide = True
        # db.commit()
    except Exception as e:
        logging.exception("Ошибка при разделении команд для текущего события: %s", e)
    finally:
        db.close()
