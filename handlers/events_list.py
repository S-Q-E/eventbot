from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration, User

event_list_router = Router()
EVENTS_PER_PAGE = 3


@event_list_router.callback_query(F.data.startswith("events_list"))
@event_list_router.callback_query(F.data.startswith("events_page_"))
async def list_events(callback: types.CallbackQuery):
    """
    Отображает список всех событий с пагинацией и динамической кнопкой регистрации.
    """
    # Получение текущей страницы из callback_data
    try:
        page = int(callback.data.split("_")[-1])
    except ValueError:
        page = 1

    db = next(get_db())
    events = db.query(Event).order_by(Event.event_time.asc()).all()

    # Проверка наличия событий
    if not events:
        await callback.message.answer("Нет доступных событий.")
        return

    # Расчет страниц и событий на текущей странице
    total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE  # Округление вверх
    page = max(1, min(page, total_pages))  # Ограничение страницы в рамках допустимого
    events_to_show = events[(page - 1) * EVENTS_PER_PAGE:page * EVENTS_PER_PAGE]

    # Вывод событий на текущей странице
    user_id = callback.from_user.id
    for event in events_to_show:
        # Проверка, зарегистрирован ли пользователь на событие
        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event.id).first()

        # Динамическое определение кнопки регистрации
        if registration:
            join_button = InlineKeyboardButton(
                text="❌ Отменить запись",
                callback_data=f"cancel_registration_{event.id}"
            )
        else:
            join_button = InlineKeyboardButton(
                text="☑️ Записаться",
                callback_data=f"join_{event.id}"
            )

        # Сбор информации о зарегистрированных пользователях
        registrations = db.query(Registration).filter_by(event_id=event.id).all()
        registered_users = [
            f"{user.first_name} {user.last_name}" for reg in registrations
            if (user := db.query(User).filter_by(id=reg.user_id).first())
        ]
        registered_users_text = "\n".join(registered_users) if registered_users else "Нет участников"

        show_on_map = InlineKeyboardButton(
            text="📍 Показать на карте",
            callback_data=f"show_on_map_{event.id}"
        )
        event_details = InlineKeyboardButton(
            text="📄 Подробнее",
            callback_data=f"details_{event.id}"
        )

        markup = InlineKeyboardMarkup(inline_keyboard=[[event_details], [join_button], [show_on_map]])
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
    pagination_markup = InlineKeyboardMarkup(inline_keyboard=[pagination_buttons])
    await callback.message.answer(f"Страница {page}/{total_pages}", reply_markup=pagination_markup)


@event_list_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    """
    Обрабатывает отмену регистрации на событие.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    db = next(get_db())

    # Удаляем регистрацию
    registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    event = db.query(Event).filter_by(id=event_id).first()

    if registration:
        db.delete(registration)
        event.current_participants -= 1
        db.commit()
        await callback_query.message.answer("Вы успешно отменили регистрацию на это событие.")
        await callback_query.message.answer(f"Освободилось 1 место на событие {event.name}.")
    else:
        await callback_query.answer("Вы не были записаны на это событие.")