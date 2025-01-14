# from datetime import datetime
# from sqlalchemy.orm import Session, joinedload
# from db.database import Registration, User, Event
#
#
# def get_users_for_feedback(db: Session, event_id: int):
#     """
#     Получает список пользователей, которым нужно отправить запрос на отзыв.
#
#     Args:
#         db: Объект сессии базы данных SQLAlchemy.
#         event_id: ID события.
#
#     Returns:
#         Список пользователей, которым нужно отправить запрос.
#     """
#     registrations = (
#         db.query(Registration)
#         .filter(
#             Registration.event_id == event_id,
#             Registration.has_given_feedback == False  # Только пользователи без отзыва
#         )
#         .join(User, Registration.user_id == User.id)
#         .all()
#     )
#     return [reg.user for reg in registrations]
#
#
# def get_started_events(db: Session):
#     """
#     Получает начавшиеся события с пользователями, которым нужно отправить уведомление о предоставлении отзыва.
#
#     Args:
#         db: Объект сессии базы данных SQLAlchemy.
#
#     Returns:
#         Список словарей с id и именем начавшихся событий.
#     """
#     current_time = datetime.now()
#
#     events = (
#         db.query(Event)
#         .join(Registration, Event.id == Registration.event_id)  # Присоединяем регистрации
#         .filter(
#             Event.event_time <= current_time,                 # Событие уже началось
#             Registration.has_given_feedback == False          # Пользователь ещё не оставил отзыв
#         )
#         .options(joinedload(Event.registrations))             # Подгружаем регистрации
#         .distinct()                                           # Убираем дубли
#         .all()
#     )
#
#     started_events = [{"id": event.id, "name": event.name} for event in events]
#     return started_events
#
#
