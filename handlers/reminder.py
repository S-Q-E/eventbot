from aiogram import Router, types
from db.database import get_db, Registration
from aiogram.filters.callback_data import CallbackData


# Создаем Router для напоминаний
reminder_router = Router()


class ReminderCallback(CallbackData, prefix="set_reminder"):
    time_before_event: str
    event_id: int


# Установка времени напоминания
@reminder_router.callback_query(lambda c: c.data.startswith("set_reminder"))
async def set_reminder(callback_query: types.CallbackQuery, callback_data: ReminderCallback):
    reminder_type = callback_query.data.split('_')[2]
    event_id = callback_query.data.split('_')[-1]
    user_id = callback_query.from_user.id
    db = next(get_db())

    registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()

    if registration:
        # Устанавливаем время напоминания в зависимости от типа
        if reminder_type == "1h":
            registration.reminder_time = "1h"
        elif reminder_type == "2h":
            registration.reminder_time = "2h"
        elif reminder_type == "1d":
            registration.reminder_time = "1d"

        db.commit()
        await callback_query.message.answer(f"Напоминание установлено за {callback_data.time_before_event} до события.")
    else:
        await callback_query.message.answer("Вы не записаны на это событие.")
