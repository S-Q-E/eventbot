# import logging
# from aiogram import Bot
# from db.database import get_db
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from utils.get_expired_eventid import get_users_for_feedback
#
#
# async def send_feedback_request(bot: Bot, event_id: int, event_name: str):
#     """
#     Отправляет пользователям запросы на отзывы по завершившемуся событию.
#     """
#     try:
#         db = next(get_db())
#         get_feedback = InlineKeyboardMarkup(inline_keyboard=[
#             [
#                 InlineKeyboardButton(text="💬 Оставить отзыв", callback_data=f"send_feedback_{event_id}"),
#                 InlineKeyboardButton(text="🚫 Не хочу оставлять отзыв", callback_data=f"feedback_decline_{event_id}")
#             ]
#         ])
#         users = get_users_for_feedback(db, event_id)
#         for user in users:
#             if user:
#                 await bot.send_message(
#                     chat_id=user.id,
#                     text=f"Спасибо, что приняли участие в событии \"{event_name}\"! Пожалуйста, оставьте отзыв о событии.",
#                     reply_markup=get_feedback
#                 )
#                 logging.info(f"Отправлены запросы на отзывы для события \"{event_name}\".")
#
#     except Exception as e:
#         logging.info(f"Ошибка при отправке запроса на отзывы {e}")
