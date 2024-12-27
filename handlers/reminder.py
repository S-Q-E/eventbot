from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db.database import get_db, Registration

reminder_router = Router()


@reminder_router.callback_query(F.data.startswith('notify_'))
async def set_notification_preference(callback: types.CallbackQuery):
    back_btn = InlineKeyboardButton(text="Назад", callback_data="events_page_1")
    markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
    user_id = callback.from_user.id
    _, notify_time, event_id = callback.data.split('_')

    db = next(get_db())
    registration = db.query(Registration).filter_by(user_id=user_id, event_id=int(event_id)).first()

    if not registration:
        await callback.answer("Ошибка: регистрация на событие не найдена.")
        return

    registration.reminder_time = notify_time
    db.commit()

    reminder_text = "день" if notify_time == "24h" else "2 часа"
    await callback.message.answer(f"Вы выбрали напоминание за {reminder_text} до события.", show_alert=True, reply_markup=markup)