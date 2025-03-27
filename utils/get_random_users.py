# import random
# import logging
# from sqlalchemy.exc import SQLAlchemyError
# from db.database import get_db, Registration
#
#
# def get_random_user(event_id):
#     db = next(get_db())
#     try:
#         registrations = db.query(Registration).filter_by(event_id=event_id).all()
#         if not registrations:
#             logging.warning("Нет доступных регистрации")
#             return
#         selected_reg: Registration = random.choice(registrations)
#         new_candidate = MVPCandidate(event_id=event_id,
#                                      user_id=selected_reg.user_id,
#                                      is_selected=True)
#         db.add(new_candidate)
#         db.commit()
#         return True
#     except SQLAlchemyError as e:
#         logging.info(f"Ошибка при получении данных: {e}")
#         return False
#     finally:
#         db.close()
#
#
# def check_and_process_events():
#     """
#     Проверяет начавшиеся события и запускает функцию отправки уведомления о начале голосования
#     :return:
#     """
#     with next(get_db()) as db:
#         active_event_ids = get_active_events()
#
#         if not active_event_ids:
#             return
#
#         for event_id in active_event_ids:
#             logging.info(f"Началось событие c ID {event_id}")
#             process_event(event_id)
#
#
# async def process_event(event_id):
#     """
#     Обрабатывает начавшееся событие.
#     Тут мы запускаем получение рандомного пользователя
#     :param event_id: int
#     :return: True or False
#     """
#     try:
#         result = get_random_user(event_id)
#         if result:
#             return True
#     except Exception as e:
#         logging.info(f"Произошла ошибка при выборе случайного пользователя {e}")
#         return
