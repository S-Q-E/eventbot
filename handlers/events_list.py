from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError
from db.database import get_db, Event, Registration, User
from utils.get_week_day import get_week_day

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
    for event in events_to_show:
        # Проверка, зарегистрирован ли пользователь на событие
        event_details = InlineKeyboardButton(
            text="📄 Подробнее",
            callback_data=f"details_{event.id}"
        )
        date = event.event_time
        weekday = get_week_day(date)
        markup = InlineKeyboardMarkup(inline_keyboard=[[event_details]])
        await callback.message.answer(
            f"🎉 <b>{event.name}</b>\n"
            f"🕒 <b>Дата:</b> {weekday} {event.event_time.strftime('%d %B') } \n",
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
    Обрабатывает отмену регистрации на событие и уведомляет других участников.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    db = next(get_db())
    go_to_event = InlineKeyboardButton(text="Перейти к событию ➡️", callback_data=f"details_{event_id}")
    markup = InlineKeyboardMarkup(inline_keyboard=[[go_to_event]])
    try:
        # Проверка регистрации пользователя на событие
        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if not event:
            await callback_query.answer("Событие не найдено.")
            return

        if registration:
            # Удаляем регистрацию и уменьшаем счетчик участников
            db.delete(registration)
            event.current_participants -= 1
            db.commit()

            await callback_query.message.answer("Вы успешно отменили регистрацию на это событие.")

            # Уведомляем других участников
            registrations = db.query(Registration).filter_by(event_id=event_id).all()
            for reg in registrations:
                try:
                    await callback_query.bot.send_message(
                        chat_id=reg.user_id,
                        text=f"⚠️ Освободилось место на событие '{event.name}'! Спешите зарегистрироваться, пока оно не занято.",
                        reply_markup=markup
                    )
                except TelegramAPIError as e:
                    print(f"Ошибка отправки уведомления пользователю {reg.user_id}: {e}")

        else:
            await callback_query.answer("Вы не были записаны на это событие.")
    except Exception as e:
        print(f"Ошибка при отмене регистрации: {e}")
        await callback_query.message.answer("Произошла ошибка при отмене регистрации.")
    finally:
        db.close()