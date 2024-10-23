from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Registration, Event
from handlers.reminder import ReminderCallback

event_join_router = Router()


@event_join_router.callback_query(F.data.startswith("join_"))
async def join_event(callback_query : types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    try:
        event_id = int(callback_query.data.split("join_")[1])
    except (IndexError, ValueError):
        await callback_query.message.answer("Ошибка: неверный формат данных события.")
        return
    user_id = callback_query.from_user.id
    db = next(get_db())

    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        await callback_query.message.answer("Событие не найдено")

    if event.current_participants >= event.max_participants:
        await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
        return

    # Проверка, что пользователь еще не записан на это событие
    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    if existing_registration:
        await callback_query.message.answer("Вы уже записаны на это событие.")
        return

    # Записываем пользователя на событие
    new_registration = Registration(user_id=user_id, event_id=event_id)
    db.add(new_registration)
    event.current_participants += 1
    db.commit()

    # После записи предлагается выбрать напоминание
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

    markup = InlineKeyboardMarkup(inline_keyboard=[[reminder_1h], [reminder_2h], [reminder_1d]])

    await callback_query.message.answer("Вы записаны! Установите напоминание:", reply_markup=markup)

