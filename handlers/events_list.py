from aiogram import Router, types,F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration, User

event_list_router = Router()


@event_list_router.message(Command("events_list"))
@event_list_router.callback_query(F.data == 'events')
async def list_events(message_or_callback: types.Message | types.CallbackQuery):
    """
    Функция отображает список всех событий.
    Может быть вызвана как по команде /events_list, так и по нажатию на кнопку "События".
    """
    # await message_or_callback.edit_reply_markup()
    # Определяем, что было получено: сообщение или callback
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback

    db = next(get_db())
    events = db.query(Event).all()

    if events:
        for event in events:
            registrations = db.query(Registration).filter_by(event_id=event.id).all()
            registered_users = []
            for registration in registrations:
                user = db.query(User).filter_by(id=registration.user_id).first()
                if user:
                    registered_users.append(f"{user.first_name} {user.last_name}")

            # Формирование текста с информацией о пользователях
            registered_users_text = "\n".join(
                registered_users) if registered_users else "Нет зарегистрированных участников"
            show_on_map = InlineKeyboardButton(
                text="Показать на карте",
                callback_data=f"show_on_map_{event.id}"
            )
            join_button = InlineKeyboardButton(
                text="Записаться",
                callback_data=f"join_{event.id}"
            )

            markup = InlineKeyboardMarkup(inline_keyboard=[[join_button], [show_on_map]])
            await message.answer(
                f"🎉 <b>{event.name}</b>\n"
                f"🕒 <b>Дата:</b> {event.event_time.strftime('%d %B')} \n\n"
                f"📝 <b>Описание:</b> {event.description}\n"
                f"💰 <b>Цена:</b> {event.price}\n"
                f"💡 <b>Осталось мест:</b> {event.max_participants - event.current_participants}\n\n"
                f"👥 <b>Зарегистрированные участники:</b>\n{registered_users_text}",
                reply_markup=markup,
                parse_mode="HTML"
            )
    else:
        await message.answer("Нет доступных событий.")

