import logging
from aiogram import Bot
from db.database import get_db, Registration
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def send_feedback_request(bot: Bot, event_id: int, event_name: str):
    """
    Отправляет пользователям запросы на отзывы по завершившемуся событию.
    """
    try:
        db = next(get_db())
        registrations = db.query(Registration).filter_by(event_id=event_id).all()

        get_feedback = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Оставить отзыв", callback_data=f"send_feedback_{event_id}")
            ]
        ])

        for registration in registrations:
            user_id = registration.user_id
            await bot.send_message(
                chat_id=user_id,
                text=f"Спасибо, что приняли участие в событии \"{event_name}\"! Пожалуйста, оставьте отзыв о событии.",
                reply_markup=get_feedback
            )
        logging.info(f"Отправлены запросы на отзывы для события \"{event_name}\".")
    except Exception as e:
        logging.info(f"Ошибка при отправке запроса на отзывы {e}")