import logging

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration, User

my_event_router = Router()


@my_event_router.callback_query(F.data == 'my_events')
async def my_events(callback: types.CallbackQuery):
    """
    Отображает список событий, на которые пользователь записан, с возможностью отменить участие
    и показывает список других участников.
    """
    user_id = callback.from_user.id
    db = next(get_db())
    registrations = db.query(Registration).filter_by(user_id=user_id).all()

    if registrations:
        for reg in registrations:
            event = db.query(Event).filter_by(id=reg.event_id).first()
            if event is None:
                logging.warning(f"Событие с ID {reg.event_id} не найдено. Пропускаем.")
                continue

                # Получаем список участников для текущего события
            participants = db.query(User).join(Registration, User.id == Registration.user_id) \
                .filter(Registration.event_id == event.id).all()
            participants_list = "\n".join(
                f"{user.first_name} {user.last_name}" for user in participants
            ) or "Нет участников"

            # Создаем кнопку "Я не пойду"
            cancel_button = InlineKeyboardButton(
                text="Я не пойду",
                callback_data=f"cancel_registration_{reg.event_id}"
            )
            markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])

            await callback.message.answer(
                f"Вы записаны на: <b>{event.name}</b> — {event.event_time.strftime('%d %A')}\n\n"
                f"👥 <b>Участники события:</b>\n{participants_list}",
                reply_markup=markup,
                parse_mode='HTML'
            )
    else:
        await callback.message.answer("У вас нет активных записей.")

#
# @my_event_router.message(Command("my_events"))
# async def my_events(message: types.Message):
#     """
#     Отображает список событий, на которые пользователь записан, с возможностью отменить участие
#     и показывает список других участников.
#     """
#     user_id = message.from_user.id
#     db = next(get_db())
#     registrations = db.query(Registration).filter_by(user_id=user_id).all()
#
#     if registrations:
#         for reg in registrations:
#             event = db.query(Event).filter_by(id=reg.event_id).first()
#
#             # Получаем список участников для текущего события
#             participants = db.query(User).join(Registration, User.id == Registration.user_id) \
#                 .filter(Registration.event_id == event.id).all()
#             participants_list = "\n".join(
#                 f"{user.first_name} {user.last_name}" for user in participants
#             ) or "Нет участников"
#
#             # Создаем кнопку "Я не пойду"
#             cancel_button = InlineKeyboardButton(
#                 text="Я не пойду",
#                 callback_data=f"cancel_registration_{reg.event_id}"
#             )
#             markup = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
#
#             await message.answer(
#                 f"Вы записаны на: <b>{event.name}</b> — {event.event_time.strftime('%d %A')}\n\n"
#                 f"👥 <b>Участники события:</b>\n{participants_list}",
#                 reply_markup=markup,
#                 parse_mode='HTML'
#             )
#     else:
#         await message.answer("У вас нет активных записей.")


# Обработчик для кнопки "Я не пойду"
@my_event_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    """
    Обрабатывает отмену регистрации на событие.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    db = next(get_db())

    # Удаляем регистрацию
    registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    event = db.query(Event).filter_by(id=event_id).first()

    if registration:
        db.delete(registration)
        event.current_participants -= 1
        db.commit()
        await callback_query.answer("Вы успешно отменили регистрацию на это событие.")
        await callback_query.message.answer(f"Освободилось 1 место на событие {event.name}.")
    else:
        await callback_query.answer("Вы не были записаны на это событие.")


