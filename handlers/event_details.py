from aiogram import types, F, Router
from db.database import get_db, Event
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
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

        # Кнопка для записи на событие
        register_button = InlineKeyboardButton(text="📝 Записаться", callback_data=f"join_{event_id}")
        back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="events_list")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[register_button], [back_button]])

        await callback.message.answer(event_info, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка в event_details.py: {e}")
        await callback.answer("Произошла ошибка при загрузке события.", show_alert=True)
