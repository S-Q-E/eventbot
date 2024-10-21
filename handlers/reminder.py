from aiogram import Router, types
from db.database import get_db, Registration
from aiogram.filters.callback_data import CallbackData

# Создаем Router для напоминаний
reminder_router = Router()


class ReminderCallback(CallbackData, prefix="set_reminder"):
    time_before_event: str
    event_id: int


# Установка времени напоминания
@reminder_router.callback_query(ReminderCallback.filter())
async def set_reminder(callback_query: types.CallbackQuery, callback_data: ReminderCallback):
    await callback_query.message.edit_reply_markup(reply_markup=None)

    user_id = callback_query.from_user.id
    event_id = callback_data.event_id  # Берем event_id напрямую из callback_data
    time_before_event = callback_data.time_before_event  # Берем время напоминания напрямую из callback_data

    db = next(get_db())

    # Поиск регистрации пользователя на событие
    registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()

    if registration:
        # Устанавливаем время напоминания в зависимости от типа
        registration.reminder_time = time_before_event
        db.commit()

        await callback_query.message.answer(f"Напоминание установлено за {time_before_event} до события.")
    else:
        await callback_query.message.answer("Вы не записаны на это событие.")
