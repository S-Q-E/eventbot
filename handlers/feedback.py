# import logging
# from aiogram import Router, types, F
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from aiogram.fsm.state import StatesGroup, State
# from aiogram.fsm.context import FSMContext
# from db.database import get_db, Feedback, Event, Registration
#
# feedback_router = Router()
#
#
# class GetFeedbackForm(StatesGroup):
#     wait_feedback_text = State()
#
#
# @feedback_router.callback_query(F.data.startswith("send_feedback_"))
# async def handle_feedback_text(callback: types.CallbackQuery, state: FSMContext):
#     db = next(get_db())
#     try:
#         event_id = int(callback.data.split("_")[-1])
#         event = db.query(Event).filter(Event.id == event_id).first()
#         if not event:
#             await callback.message.answer("Событие не найдено")
#             logging.info(f"Событие с ID {event.id} не найдено")
#         await callback.message.edit_text(f"Пожалуйста напишите свой отзыв о событий {event.name}")
#         user_id = callback.from_user.id
#         await state.update_data(user_id=user_id,
#                                 event_id=event_id)
#         await state.set_state(GetFeedbackForm.wait_feedback_text)
#     except Exception as e:
#         await callback.message.answer("Ошибка id события")
#         logging.info(f"Ошибка в feedback.py. Неверный ID {e}")
#
#
# @feedback_router.message(GetFeedbackForm.wait_feedback_text)
# async def process_feedback_text(message: types.Message, state: FSMContext):
#     feedback_text = message.text
#     await state.update_data(feedback_text=feedback_text)
#     data = await state.get_data()
#     event_id = data.get("event_id")
#     await message.answer(
#         "Спасибо за ваш отзыв! ⬆️Теперь поставьте оценку событию от 1 до 5:",
#         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}_{event_id}") for i in range(1, 6)]
#         ])
#     )
#
#
# @feedback_router.callback_query(F.data.startswith("rate_"))
# async def handle_feedback_rating(callback_query: types.CallbackQuery, state: FSMContext):
#     callback_data = callback_query.data.split("_")
#     rating = int(callback_data[1])
#     event_id = int(callback_data[2])
#
#     # Извлечение данных из состояния
#     data = await state.get_data()
#     user_id = data.get("user_id")
#     feedback_text = data.get("feedback_text")
#
#     # Проверяем, есть ли все необходимые данные
#     if not user_id or feedback_text is None:
#         await callback_query.message.answer("Ошибка: отсутствуют данные для сохранения отзыва.")
#         logging.error("Отсутствуют данные для обработки отзыва.")
#         return
#
#     try:
#         with next(get_db()) as db:
#             feedback = db.query(Feedback).filter_by(user_id=user_id, event_id=event_id).first()
#             if feedback:
#                 feedback.rating = rating
#             else:
#                 new_feedback = Feedback(event_id=event_id, user_id=user_id, review=feedback_text, rating=rating)
#                 db.add(new_feedback)
#
#             registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
#             if registration:
#                 registration.has_given_feedback = True
#
#             db.commit()
#
#         await callback_query.message.edit_text(
#             "Спасибо за вашу оценку! Мы рады, что вы выбрали EventBot.",
#             reply_markup=InlineKeyboardMarkup(
#                 inline_keyboard=[[InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]]
#             )
#         )
#     except Exception as e:
#         logging.exception(f"Ошибка при создании/обновлении отзыва: {e}")
#         await callback_query.message.answer("Произошла ошибка при обработке вашего отзыва. Пожалуйста, попробуйте позже.")
#     finally:
#         await state.clear()
#
#
# @feedback_router.callback_query(F.data.startswith("feedback_decline_"))
# async def decline_feedback(callback_query: types.CallbackQuery):
#     """
#     Обрабатывает отказ пользователя от оставления отзыва.
#     """
#     event_id = int(callback_query.data.split("_")[-1])
#     user_id = callback_query.from_user.id
#
#     try:
#         with next(get_db()) as db:
#             registration = (
#                 db.query(Registration)
#                 .filter(
#                     Registration.event_id == event_id,
#                     Registration.user_id == user_id
#                 )
#                 .first()
#             )
#
#             if registration:
#                 # registration.has_given_feedback = True
#                 db.commit()
#                 logging.info(f"Пользователь {user_id} отказался от отзыва по событию {event_id}.")
#             else:
#                 logging.warning(f"Регистрация для пользователя {user_id} и события {event_id} не найдена.")
#                 await callback_query.message.answer("Вы не зарегистрированы на это событие.")
#                 return
#
#         await callback_query.message.edit_text("Спасибо, мы учли ваш ответ!")
#     except Exception as e:
#         logging.exception(f"Ошибка при обработке отказа: {e}")
#         await callback_query.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
