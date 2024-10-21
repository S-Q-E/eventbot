from aiogram import Router, types,F
from db.database import get_db, Event, Registration

my_event_router = Router()


# Мои записи
@my_event_router.callback_query(F.data == 'my_events')
async def my_events(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    user_id = callback_query.from_user.id
    db = next(get_db())
    registrations = db.query(Registration).filter_by(user_id=user_id).all()

    if registrations:
        for reg in registrations:
            event = db.query(Event).filter_by(id=reg.event_id).first()
            await callback_query.message.answer(f"Вы записаны на: {event.name} — {event.event_time}")
    else:
        await callback_query.message.answer("У вас нет активных записей.")