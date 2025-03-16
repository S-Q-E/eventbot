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
        # 1. Получаем 3 последних MVP-кандидатов (без привязки к event_id)
        candidates = (
            db.query(MVPCandidate)
            .options(joinedload(MVPCandidate.user))  # Оптимизация запроса
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
