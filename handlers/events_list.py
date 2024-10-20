from aiogram import Router, types,F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event

event_list_router = Router()


# Отображение всех событий
@event_list_router.callback_query(F.data == 'events')
async def list_events(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer("Список событий...")
    db = next(get_db())
    events = db.query(Event).all()

    if events:
        for event in events:
            join_button = InlineKeyboardButton(
                text="Записаться",
                callback_data='events_list'
            )
            markup = InlineKeyboardMarkup(inline_keyboard=[[join_button]])
            await callback_query.message.answer(
                f"{event.name} — {event.event_time}",
                reply_markup=markup
            )
    else:
        await callback_query.message.answer("Нет доступных событий.")

