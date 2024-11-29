from aiogram import types, F, Router
from db.database import get_db, Event, Registration  # Добавим импорт модели Registration
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

event_detail_router = Router()


@event_detail_router.callback_query(F.data.startswith("details_"))
async def event_details(callback: types.CallbackQuery):
    """
    Отображает детальное описание события
    """
    try:
        # Получаем ID события из callback data
        event_id = int(callback.data.split("_")[-1])
        db = next(get_db())
        event = db.query(Event).filter_by(id=event_id).first()

        # Проверяем, существует ли событие
        if not event:
            await callback.answer("❗ Событие не найдено.", show_alert=True)
            return

        # Проверка, зарегистрирован ли пользователь на событие
        user_id = callback.from_user.id
        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()

        # Формирование текста кнопки в зависимости от статуса регистрации
        if registration:
            action_button = InlineKeyboardButton(
                text="❌ Отменить запись",
                callback_data=f"cancel_registration_{event_id}"
            )
        else:
            action_button = InlineKeyboardButton(
                text="📝 Записаться",
                callback_data=f"join_{event_id}"
            )

        # Форматирование времени события
        formatted_time = event.event_time.strftime("%d.%m.%Y %H:%M")

        # Формирование сообщения с информацией о событии
        event_info = (
            f"<b>📅 {event.name}</b>\n\n"
            f"📝 <b>Описание:</b> {event.description}\n\n"
            f"📍 <b>Адрес:</b> {event.address}\n"
            f"🕒 <b>Время:</b> {formatted_time}\n"
            f"💰 <b>Цена:</b> {event.price} руб.\n"
            f"👥 <b>Участников:</b> {event.current_participants}/{event.max_participants}"
        )

        # Кнопки действия и возврата
        back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="events_list")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[action_button], [back_button]])

        await callback.message.answer(event_info, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка в event_details.py: {e}")
        await callback.answer("Произошла ошибка при загрузке события.", show_alert=True)
