import random
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from db.database import get_db, Event, Registration, User, VotingSession
from datetime import datetime

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")
ADMIN = os.getenv("ADMIN_2")


def get_started_events():
    db = next(get_db())
    try:
        event = db.query(Event).all()
        if not event:
            return False
        now = datetime.now()
        events = db.query(Event).filter(
            Event.event_time < now,
            Event.is_checked == False
        ).all()
        for event in events:
            candidate = choose_mvp_candidate(event.id)
            if candidate:
                logging.info(f"Выбран MVP-кандидат для события {event.id}: {candidate.id}")
            else:
                logging.info(f"Не найден кандидат для события {event.id}")
            event.is_checked = True
        db.commit()
    except SQLAlchemyError as e:
        logging.warning(f"Ошибка в get_started_events. {e}")
        db.rollback()
    except Exception as e:
        logging.warning(f"Ошибка в get_started_events. {e}")
        db.rollback()
    finally:
        db.close()


def choose_mvp_candidate(event_id: int):
    """
    Выбирает одного пользователя из регистраций для указанного события, у которого is_mvp_candidate==False.
    Устанавливает флаг is_mvp_candidate=True и возвращает выбранного пользователя.
    """
    db = next(get_db())
    try:
        registrations = db.query(Registration).filter(
            Registration.event_id == event_id,
            Registration.user.has(User.is_mvp_candidate == False)
        ).all()
        if not registrations:
            logging.info("Нет пользователей для выбора кандидата.")
            return None

        selected_registration = random.choice(registrations)
        selected_registration.user.is_mvp_candidate = True
        db.commit()
        return selected_registration.user
    except SQLAlchemyError as e:
        logging.error(f"Ошибка при выборе MVP-кандидата: {e}")
        db.rollback()
    finally:
        db.close()
    return None


def announce_winner():
    """
    Определяет победителя голосования по событию.
    Возвращает пользователя-победителя, а затем сбрасывает флаги is_mvp_candidate и счетчики голосов.
    """
    db: Session = next(get_db())
    try:
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        if not candidates:
            logging.info("Нет кандидатов")
            return None

        winner = max(candidates, key=lambda user: user.votes)
        winner_photo_id = winner.photo_file_id
        winner_name =f"{winner.first_name} {winner.last_name}"
        for candidate in candidates:
            candidate.is_mvp_candidate = False
            candidate.votes = 0
        db.commit()
        return winner_name, winner_photo_id
    except Exception as e:
        logging.info(f"Ошибка в announce winner {e}")
        db.rollback()
    finally:
        db.close()
    return None


async def start_voting(bot: Bot):
    """
    Обработчик команды для начала голосования.
    Извлекает всех пользователей с is_mvp_candidate==True,
    отправляет их фото (или дефолтное) и прикрепляет инлайн-клавиатуру с кнопками для голосования.
    :param bot:
    :return:
    """
    logging.info("Начинается голосование! ")
    db = next(get_db())
    try:
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        if not candidates:
            await bot.send_message(chat_id=ADMIN, text="Нет кандидатов на голосование")
        media = []
        keyboard_builder = InlineKeyboardBuilder()
        for candidate in candidates:
            display_name = f"🏆 {candidate.first_name} {candidate.last_name} ({candidate.votes})"
            photo = candidate.photo_file_id
            media.append(InputMediaPhoto(media=photo, caption=display_name))
            keyboard_builder.button(
                text=display_name,
                callback_data=f"vote_{candidate.id}"
            )
        await bot.send_media_group(chat_id=CHAT_ID, media=media)
        options = [f"{c.first_name} {c.last_name}" for c in candidates]
        print(options)
        poll_message = await bot.send_poll(
            chat_id=CHAT_ID,
            question="Кто лучший игрок?",
            options=options,
            is_anonymous=False
        )
        voting_session = VotingSession(poll_id=poll_message.poll.id)
        db.add(voting_session)
        db.commit()
    except Exception as e:
        logging.info(f"Ошибка в start_voting {e}")
        await bot.send_message(chat_id=ADMIN, text="Ошибка попробуйте позднее")
        db.rollback()
        db.close()
    finally:
        db.close()


async def end_voting(bot: Bot):
    """
    Обработчик команды для завершения голосования.
    Определяет победителя и отправляет поздравление в группу.
    """
    logging.info("Голосование закончилось. Идет подсчет голосов")
    winner_name, photo_id = announce_winner()
    if winner_name and photo_id:
        await bot.send_photo(chat_id=CHAT_ID,
                             photo=photo_id,
                             caption=f"Звание лучшего игрока недели получает\n"
                                     f" 🏆{winner_name} 🏆 \nПоздравляем!🎉🎉🎉")
    else:
        logging.info("Не удалось определить победителя")
