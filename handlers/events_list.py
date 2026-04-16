import os
import locale
import html
import logging
from datetime import datetime
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import get_db, Event, Registration, User, Category
from utils.get_week_day import get_week_day
from dotenv import load_dotenv

load_dotenv()

ADMIN = os.getenv("ADMIN_2")
ADMIN_2 = os.getenv("ADMIN_3")

event_list_router = Router()
EVENTS_PER_PAGE = 4


@event_list_router.callback_query(F.data == "events_list")
async def show_categories(callback: types.CallbackQuery):
    with get_db() as db:
        categories = db.query(Category).order_by(Category.name).all()

        if not categories:
            await callback.message.answer("Категории ещё не созданы.")
            return

        builder = InlineKeyboardBuilder()
        for cat in categories:
            builder.button(
                text=cat.name,
                callback_data=f"filter_cat_{cat.id}"
            )
        builder.button(text="Главное меню", callback_data="main_menu")
        builder.adjust(2)  # по 2 кнопки в ряд

        await callback.message.answer(
            "📂 Выберите категорию:",
            reply_markup=builder.as_markup()
        )


@event_list_router.callback_query(F.data.startswith("filter_cat_"))
async def list_events_by_category(callback: types.CallbackQuery):
    """
    Показывает события выбранной категории с пагинацией.
    Ожидает callback.data вида "filter_cat_{cat_id}_{page}".
    """
    parts = callback.data.split("_")
    try:
        cat_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Некорректный формат категории.", show_alert=True)
        return

    try:
        page = int(parts[3])
    except (IndexError, ValueError):
        page = 1

    # Получаем и фильтруем события
    now = datetime.now()
    with get_db() as db:
        events = (
            db.query(Event)
              .filter(Event.category_id == cat_id, Event.event_time > now)
              .order_by(Event.event_time.asc())
              .all()
        )

        keyboard = InlineKeyboardBuilder()

        if not events:
            keyboard.button(
                text="🔙 Категории",
                callback_data="events_list")
            await callback.message.edit_text("События в этой категории отсутствуют.", reply_markup=keyboard.as_markup())
            return

        # Пагинация
        total_pages = (len(events) + EVENTS_PER_PAGE - 1) // EVENTS_PER_PAGE
        page = max(1, min(page, total_pages))
        start = (page - 1) * EVENTS_PER_PAGE
        slice_events = events[start:start + EVENTS_PER_PAGE]

        try:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        except locale.Error:
            # Если локаль не найдена, попробуйте другую, например 'Russian'.
            locale.setlocale(locale.LC_TIME, 'Russian')
        
        # Отправляем каждое событие в отдельном сообщении
        for event in slice_events:
            weekday = get_week_day(event.event_time)
            text = (
                f"🎉 <b>{html.escape(event.name)}</b>\n"
                f"🕒 Дата:<b>{weekday} {event.event_time.strftime('%d %B')}</b>\n"
            )
            btn = types.InlineKeyboardButton(
                text="📄 Подробнее",
                callback_data=f"details_{event.id}"
            )
            await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[btn]]), parse_mode="HTML")

        # Строим клавиатуру пагинации + кнопка «Назад к категориям»
        kb_builder = InlineKeyboardBuilder()
        if page > 1:
            kb_builder.button(
                text="⬅️ Предыдущая",
                callback_data=f"filter_cat_{cat_id}_{page - 1}"
            )
        if page < total_pages:
            kb_builder.button(
                text="Следующая ➡️",
                callback_data=f"filter_cat_{cat_id}_{page + 1}"
            )
        # Кнопка возврата к списку категорий
        kb_builder.button(
            text="🔙 Категории",
            callback_data="events_list"
        )
        # Разместим навигацию в одну строку
        kb_builder.adjust(3)

        # Финальное сообщение с навигацией
        await callback.message.answer(
            f"Страница {page}/{total_pages}",
            reply_markup=kb_builder.as_markup()
        )


@event_list_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    """
    Обработчик запроса на отмену регистрации — сначала спрашивает подтверждение.
    """
    event_id = int(callback_query.data.split("_")[-1])

    confirmation_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить отмену", callback_data=f"confirm_cancel_{event_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"back_to_event_list_{event_id}")
        ]
    ])

    await callback_query.message.edit_text(
        "Вы уверены, что хотите отменить регистрацию на это событие?",
        reply_markup=confirmation_markup,
        parse_mode="HTML"
    )


@event_list_router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel_registration(callback_query: types.CallbackQuery):
    """
    Реально отменяет регистрацию после подтверждения.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    try:
        with get_db() as db:
            registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
            event = db.query(Event).filter_by(id=event_id).first()

            if not event:
                await callback_query.answer("Событие не найдено.")
                return

            if registration:
                user_name = f"{html.escape(registration.user.first_name or '')} {html.escape(registration.user.last_name or '')}".strip()
                await callback_query.bot.send_message(
                    ADMIN,
                    f"Пользователь {user_name} отменил запись на событие {html.escape(event.name)}",
                    parse_mode="HTML"
                )
                if ADMIN_2:
                    await callback_query.bot.send_message(
                        ADMIN_2,
                        f"Пользователь {user_name} отменил запись на событие {html.escape(event.name)}",
                        parse_mode="HTML"
                    )

                db.delete(registration)
                event.current_participants -= 1
                # db.commit() is automatic

                await callback_query.message.edit_text("Вы успешно отменили регистрацию на это событие.")

                # Уведомляем других участников
                registrations = db.query(Registration).filter_by(event_id=event_id).all()
                for reg in registrations:
                    try:
                        go_to_event = InlineKeyboardButton(
                            text="Перейти к событию ➡️",
                            callback_data=f"details_{event_id}"
                        )
                        markup = InlineKeyboardMarkup(inline_keyboard=[[go_to_event]])

                        await callback_query.bot.send_message(
                            chat_id=reg.user_id,
                            text=f"⚠️ Освободилось место на событие {html.escape(event.name)}! Спешите зарегистрироваться!",
                            reply_markup=markup,
                            parse_mode="HTML"
                        )
                    except TelegramAPIError as e:
                        logging.error(f"Ошибка отправки уведомления пользователю {reg.user_id}: {e}")
            else:
                await callback_query.answer("Вы не были записаны на это событие.")
    except Exception as e:
        logging.error(f"Ошибка при отмене регистрации: {e}")
        await callback_query.message.answer("Произошла ошибка при отмене регистрации.")


@event_list_router.callback_query(F.data.startswith("back_to_event_list"))
async def back_to_event_list(callback: types.CallbackQuery):
    event_id = int(callback.data.split("_")[-1])
    with get_db() as db:
        event = db.query(Event).filter_by(id=event_id).first()
        if not event:
            await callback.answer("Событие не найдено!", show_alert=True)
            return
        date = event.event_time
        weekday = get_week_day(date)
        event_name = html.escape(event.name)
        event_date = event.event_time.strftime('%d %B')

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Подробнее",
                    callback_data=f"details_{event.id}"
                )
            ]
        ])
        await callback.message.edit_text(
            f"🎉 <b>{event_name}</b>\n"
            f"🕒 <b>Дата:</b> {weekday} {event_date}\n",
            reply_markup=markup,
            parse_mode="HTML"
        )
