from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration, User

event_list_router = Router()
EVENTS_PER_PAGE = 3


@event_list_router.message(Command("events_list"))
@event_list_router.callback_query(F.data.startswith("events_page_"))
async def list_events(message_or_callback: types.Message | types.CallbackQuery):
    """
    Отображает список всех событий с пагинацией и сортировкой по времени.
    """

    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    message = message_or_callback.message if is_callback else message_or_callback
    page = int(message_or_callback.data.split("events_page_")[-1])
    db = next(get_db())
    events = db.query(Event).order_by(Event.event_time.asc()).all()

    if events:
        total_pages = len(events) // EVENTS_PER_PAGE
        events_to_show = events[(page - 1) * EVENTS_PER_PAGE:page * EVENTS_PER_PAGE]

        for event in events_to_show:
            registrations = db.query(Registration).filter_by(event_id=event.id).all()
            registered_users = [
                f"{user.first_name} {user.last_name}" for reg in registrations
                if (user := db.query(User).filter_by(id=reg.user_id).first())
            ]
            registered_users_text = "\n".join(registered_users) if registered_users else "Нет участников"

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
                f"🕒 <b>Дата:</b> {event.event_time.strftime('%d %B')} \n"
                f"💰 <b>Цена:</b> {event.price}\n"
                f"💡 <b>Осталось мест:</b> {event.max_participants - event.current_participants}\n\n"
                f"👥 <b>Зарегистрированные участники:</b>\n{registered_users_text}",
                reply_markup=markup,
                parse_mode="HTML"
            )

        # Пагинация
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️ Предыдущая", callback_data=f"events_page_{page - 1}")
            )
        if page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="Следующая ➡️", callback_data=f"events_page_{page + 1}")
            )
        if pagination_buttons:
            pagination_markup = InlineKeyboardMarkup(inline_keyboard=[pagination_buttons])
            await message.answer(f"Страница: {page}", reply_markup=pagination_markup)
    else:
        await message.answer("Нет доступных событий.")


@event_list_router.callback_query(F.data.startswith("events"))
async def list_events_callback(callback: types.CallbackQuery, page: int = 1):
    """
    Отображает список всех событий с пагинацией и сортировкой по времени.
    Эта функция нужна для обработки нажатия на кнопку "Доступные ивенты"
    """
    db = next(get_db())
    events = db.query(Event).order_by(Event.event_time.asc()).all()

    if events:
        total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
        events_to_show = events[(page - 1) * EVENTS_PER_PAGE:page * EVENTS_PER_PAGE]

        for event in events_to_show:
            registrations = db.query(Registration).filter_by(event_id=event.id).all()
            registered_users = [
                f"{user.first_name} {user.last_name}" for reg in registrations
                if (user := db.query(User).filter_by(id=reg.user_id).first())
            ]
            registered_users_text = "\n".join(registered_users) if registered_users else "Нет участников"

            show_on_map = InlineKeyboardButton(
                text="Показать на карте",
                callback_data=f"show_on_map_{event.id}"
            )
            join_button = InlineKeyboardButton(
                text="Записаться",
                callback_data=f"join_{event.id}"
            )

            markup = InlineKeyboardMarkup(inline_keyboard=[[join_button], [show_on_map]])
            await callback.message.answer(
                f"🎉 <b>{event.name}</b>\n"
                f"🕒 <b>Дата:</b> {event.event_time.strftime('%d %B')} \n"
                f"💰 <b>Цена:</b> {event.price}\n"
                f"💡 <b>Осталось мест:</b> {event.max_participants - event.current_participants}\n\n"
                f"👥 <b>Зарегистрированные участники:</b>\n{registered_users_text}",
                reply_markup=markup,
                parse_mode="HTML"
            )

        # Пагинация
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="⬅️ Предыдущая", callback_data=f"events_page_{page - 1}")
            )
        if page < total_pages:
            pagination_buttons.append(
                InlineKeyboardButton(text="Следующая ➡️", callback_data=f"events_page_{page + 1}")
            )
        if pagination_buttons:
            pagination_markup = InlineKeyboardMarkup(inline_keyboard=[pagination_buttons])
            await callback.message.answer("Страница:", reply_markup=pagination_markup)
    else:
        await callback.message.answer("Нет доступных событий.")
