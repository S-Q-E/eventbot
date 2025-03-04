# import logging
#
# from aiogram import types, F, Router
# from db.database import , get_db
#
# show_feedback_router = Router()
#
#
# @show_feedback_router.callback_query(F.data == "show_feedbacks")
# async def show_all_feedbacks(callback: types.CallbackQuery):
#     try:
#         with next(get_db()) as db:
#             all_feedbacks = db.query().all()
#             if all_feedbacks:
#                 for feedback in all_feedbacks:
#                     await callback.message.answer(f"Событие: {feedback.event.name}\n"
#                                                   f"Пользователь: {feedback.user.first_name} {feedback.user.last_name}\n"
#                                                   f"Отзыв: {feedback.review}\n"
#                                                   f"Оценка: {feedback.rating}\n")
#             else:
#                 await callback.message.answer("Нет доступных отзывов")
#     except Exception as e:
#         logging.info(f"Ошибка базы данных {e}")
#         await callback.message.answer("Ошибка базы данных")
#
