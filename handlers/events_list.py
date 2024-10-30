from aiogram import Router, types,F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event

event_list_router = Router()


@event_list_router.message(Command("events_list"))
@event_list_router.callback_query(F.data == 'events')
async def list_events(message_or_callback: types.Message | types.CallbackQuery):
    """
    Функция отображает список всех событий.
    Может быть вызвана как по команде /events_list, так и по нажатию на кнопку "События".
    """

    # Определяем, что было получено: сообщение или callback
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback

    db = next(get_db())
    events = db.query(Event).all()

    if events:
        for event in events:
            join_button = InlineKeyboardButton(
                text="Записаться",
                callback_data=f"join_{event.id}"
            )

            markup = InlineKeyboardMarkup(inline_keyboard=[[join_button]])
            await message.answer(
                f"🎉 <b>{event.name}</b>\n"
                f"🕒 <b>Дата:</b> {event.event_time.strftime('%d %B')} \n\n"            
                f"📝 <b>Описание:</b> {event.description}\n"
                f"💰 <b>Цена</b>: {event.price}\n"
                f"💡 <b>Осталось мест</b>: {event.max_participants - event.current_participants}",
                reply_markup=markup,
                parse_mode="HTML"
            )
    else:
        await message.answer("Нет доступных событий.")

