import os
import logging
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from db.database import get_db, User, MVPCandidate  # Импорты моделей

load_dotenv()

GROUP_CHAT_ID = os.getenv("CHAT_ID")
ADMIN = os.getenv("ADMIN")


async def send_mvp_poll(bot: Bot):
    """Отправляет MediaGroup с фото 3 последних кандидатов и создаёт опрос."""
    db = next(get_db())
    try:
        candidates = (
            db.query(MVPCandidate)
            .options(joinedload(MVPCandidate.user))
            .filter(MVPCandidate.is_selected == True)
            .order_by(MVPCandidate.id.desc())  # Берем последних по времени
            .limit(3)
            .all()
        )

        if len(candidates) < 3:
            logging.info(f"Недостаточно кандидатов (найдено {len(candidates)}) для голосования.")
            await bot.send_message(ADMIN, "⚠️ Недостаточно MVP-кандидатов для голосования. Проверьте данные!")
            return None, None

        media_group = []
        options = []
        user_ids = []

        for candidate in candidates:
            user = candidate.user
            if user and user.photo_file_id:
                media_group.append(InputMediaPhoto(
                    media=user.photo_file_id,
                    caption=f"{user.first_name} {user.last_name}"
                ))
                options.append(f"{user.first_name} {user.last_name}")
                user_ids.append(user.id)
            else:
                logging.warning(f"Пользователь {candidate.user_id} не имеет фото. Пропускаем.")

        if not media_group:
            logging.warning("Нет подходящих медиа для отправки.")
            return None, None

        # 2. Отправляем MediaGroup с фотографиями
        await bot.send_media_group(GROUP_CHAT_ID, media=media_group)

        # 3. Создаем и отправляем опрос
        poll_message = await bot.send_poll(
            GROUP_CHAT_ID,
            question="🏐 Выберите MVP недели:",
            options=options,
            is_anonymous=False
        )

        logging.info(f"Опрос MVP успешно отправлен (ID: {poll_message.message_id})")

        return poll_message.message_id, user_ids

    except SQLAlchemyError as e:
        logging.error(f"Ошибка базы данных при отправке опроса MVP: {e}")
        return None, None
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при отправке опроса MVP: {e}")
        return None, None
    finally:
        db.close()


async def finish_mvp_poll(bot: Bot):
    """Завершает голосование, определяет победителя и отправляет его фото."""
    db = next(get_db())
    try:
        # Получаем 3 последних кандидатов
        candidates = (
            db.query(MVPCandidate)
            .filter(MVPCandidate.is_selected == True)
            .order_by(MVPCandidate.id.desc())
            .limit(3)
            .all()
        )

        if not candidates:
            logging.warning("Нет кандидатов для завершения голосования.")
            return

        # Определяем победителя (кандидат с наибольшим числом голосов)
        winner = max(candidates, key=lambda c: c.votes, default=None)

        if not winner or winner.votes == 0:
            await bot.send_message(GROUP_CHAT_ID, "Голосование завершено, но победитель не определён.")
            return

        # Получаем данные пользователя-победителя
        user = db.query(User).filter_by(id=winner.user_id).first()

        if user and user.photo_file_id:
            media = InputMediaPhoto(media=user.photo_file_id, caption=f"🏆 MVP недели: {user.first_name} {user.last_name}! 🎉")
            await bot.send_photo(GROUP_CHAT_ID, photo=user.photo_file_id, caption=media.caption)
        else:
            await bot.send_message(GROUP_CHAT_ID, f"🏆 MVP недели: {user.first_name} {user.last_name}! 🎉 (фото "
                                                  f"отсутствует)")

        # Помечаем голосование завершённым
        for candidate in candidates:
            candidate.is_selected = False  # Сбрасываем флаг
        db.commit()

    except SQLAlchemyError as e:
        logging.error(f"Ошибка базы данных при завершении голосования: {e}")
        db.rollback()
    except Exception as e:
        logging.error(f"Ошибка при завершении голосования: {e}")
    finally:
        db.close()
