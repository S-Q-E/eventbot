from aiogram import Router, types, F
from db.database import get_db, Event, Registration, User

my_event_router = Router()


@my_event_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    """
    Обрабатывает отмену регистрации на событие.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    with next(get_db()) as db:

        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if registration:
            db.delete(registration)
            event.current_participants -= 1
            db.commit()
            await callback_query.message.answer("Вы успешно отменили регистрацию на это событие.")
            await callback_query.message.answer(f"Освободилось 1 место на событие {event.name}.")
            db.close()
        else:
            await callback_query.answer("Вы не были записаны на это событие.")

