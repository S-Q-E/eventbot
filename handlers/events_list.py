from aiogram import Router, types,F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration

event_list_router = Router()


# Отображение всех событий
@event_list_router.callback_query(F.data == 'events')
async def list_events(callback_query: types.CallbackQuery):
    db = next(get_db())
    events = db.query(Event).all()

    if events:
        for event in events:
            markup = InlineKeyboardMarkup()
            join_button = InlineKeyboardButton(
                text="Записаться",
            )
            markup.add(join_button)
            await callback_query.message.answer(
                f"{event.name} — {event.event_time}",
                reply_markup=markup
            )
    else:
        await callback_query.message.answer("Нет доступных событий.")

