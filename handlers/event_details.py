import urllib.parse
import html
from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Event, Registration, User
import logging

event_detail_router = Router()


@event_detail_router.callback_query(F.data.startswith("details_"))
async def show_event_details(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    try:
        with get_db() as db:
            event = db.query(Event).filter_by(id=event_id).first()

            if not event:
                await callback.message.answer("❗ Событие не найдено.", show_alert=True)
                return

            user_id = callback.from_user.id
            user = db.query(User).filter_by(id=user_id).first()
            is_registered = user and user.is_registered

            registration = None
            if is_registered:
                registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()

            formatted_time = event.event_time.strftime("%d.%m.%Y %H:%M")

            participants = (
                db.query(User)
                .join(Registration, User.id == Registration.user_id)
                .filter(Registration.event_id == event.id)
                .order_by(User.first_name, User.last_name)
                .all()
            )

            participants_list = "\n".join(
                f"{html.escape(user.first_name or '')} {html.escape(user.last_name or '')}".strip() for user in participants
            ) or "Нет участников"

            event_info = (
                f"<b>📅 {html.escape(event.name)}</b>\n\n"
                f"📝 <b>Описание:</b> {html.escape(event.description)}\n\n"
                f"⬆️<b>Уровень игры:</b> {html.escape(event.players_level or '')}\n"
                f"📍 <b>Адрес:</b> {html.escape(event.address)}\n"
                f"🕒 <b>Время:</b> {formatted_time}\n"
                f"💰 <b>Цена:</b> {event.price} руб.\n"
                f"👥 <b>Участников:</b> {event.current_participants}/{event.max_participants}\n"
                f"📋 <b>Список участников:\n{participants_list}</b>"
            )

            buttons = []

            if is_registered:
                if registration:
                    buttons.append([
                        InlineKeyboardButton(
                            text="❌ Отменить запись",
                            callback_data=f"cancel_registration_{event_id}"
                        )
                    ])
                else:
                    buttons.append([
                        InlineKeyboardButton(
                            text="📝 Записаться",
                            callback_data=f"join_{event_id}"
                        )
                    ])
            else:
                buttons.append([
                    InlineKeyboardButton(
                        text="🔗 Завершить регистрацию",
                        callback_data="start_reg"
                    )
                ])

            # Яндекс карты
            encoded_address = urllib.parse.quote(event.address)
            yandex_maps_url = f"https://yandex.ru/maps/?text={encoded_address}"
            buttons.append([InlineKeyboardButton(text="📍 Показать на Яндекс Картах", url=yandex_maps_url)])

            # Назад
            buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_event_list_{event.id}")])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await callback.message.edit_text(event_info, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка в event_details.py: {e}")
        await callback.message.answer("Произошла ошибка при загрузке события.", show_alert=True)
