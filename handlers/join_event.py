from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Registration
from aiogram.filters.callback_data import CallbackData

from handlers.reminder import ReminderCallback

event_join_router = Router()


@event_join_router.callback_query(CallbackData.filter())
async def join_event(callback_query: types.CallbackQuery, callback_data: CallbackData.filter()):
    event_id = callback_data.event_id
    user_id = callback_query.from_user.id
    db = next(get_db())

    # Проверка, что пользователь еще не записан на это событие
    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    if existing_registration:
        await callback_query.message.answer("Вы уже записаны на это событие.")
        return

    # Записываем пользователя на событие
    new_registration = Registration(user_id=user_id, event_id=event_id)
    db.add(new_registration)
    db.commit()

    # После записи предлагается выбрать напоминание
    markup = InlineKeyboardMarkup()
    reminder_1h = InlineKeyboardButton(
        text="За час",
        callback_data=ReminderCallback(time_before_event="1h", event_id=event_id).pack()
    )
    reminder_2h = InlineKeyboardButton(
        text="За 2 часа",
        callback_data=ReminderCallback(time_before_event="2h", event_id=event_id).pack()
    )
    reminder_1d = InlineKeyboardButton(
        text="За день",
        callback_data=ReminderCallback(time_before_event="1d", event_id=event_id).pack()
    )
    markup.add(reminder_1h, reminder_2h, reminder_1d)

    await callback_query.message.answer("Вы записаны! Установите напоминание:", reply_markup=markup)

