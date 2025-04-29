import urllib.parse
from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration, User
import logging

event_detail_router = Router()

@event_detail_router.callback_query(F.data.startswith("details_"))
async def event_details(callback: types.CallbackQuery):
    try:
        event_id = int(callback.data.split("_")[-1])
        db = next(get_db())
        event = db.query(Event).filter_by(id=event_id).first()

        if not event:
            await callback.message.answer("❗ Событие не найдено.", show_alert=True)
            return

        user_id = callback.from_user.id
        user = db.query(User).filter_by(id=user_id).first()

        if not user or not user.is_registered:
            register_button = InlineKeyboardButton(
                text="🔗 Завершить регистрацию",
                callback_data="start_reg"
            )
            await callback.message.edit_text(
                "❗ Только зарегистрированные пользователи могут записываться на события.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[register_button]])
            )
            return

        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()

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

        formatted_time = event.event_time.strftime("%d.%m.%Y %H:%M")

        participants = db.query(User).join(Registration, User.id == Registration.user_id) \
            .filter(Registration.event_id == event.id).all()
        participants_list = "\n".join(
            f"{user.first_name} {user.last_name}" for user in participants
        ) or "Нет участников"

        event_info = (
            f"<b>📅 {event.name}</b>\n\n"
            f"📝 <b>Описание:</b> {event.description}\n\n"
            f"📍 <b>Адрес:</b> {event.address}\n"
            f"🕒 <b>Время:</b> {formatted_time}\n"
            f"💰 <b>Цена:</b> {event.price} руб.\n"
            f"👥 <b>Участников:</b> {event.current_participants}/{event.max_participants}\n"
            f"📋 <b>Список участников:\n{participants_list} \n</b> "
        )

        # Кодируем адрес для использования в URL
        encoded_address = urllib.parse.quote(event.address)
        yandex_maps_url = f"https://yandex.ru/maps/?text={encoded_address}"

        show_on_map = InlineKeyboardButton(
            text="📍 Показать на Яндекс Картах",
            url=yandex_maps_url
        )
        back_button = InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"back_to_event_list_{event.id}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[action_button], [show_on_map], [back_button]])

        await callback.message.edit_text(event_info, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в event_details.py: {e}")
        await callback.message.answer("Произошла ошибка при загрузке события.", show_alert=True)
