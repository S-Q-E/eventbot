import asyncio
import logging
import os
import html
from datetime import datetime

from aiogram import Router, types, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from yookassa import Payment, Configuration

from db.database import get_db, Registration, Event, User

load_dotenv()

ADMIN = os.getenv("ADMIN_2")
ADMIN_2 = os.getenv("ADMIN_3")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")

logger = logging.getLogger(__name__)
event_join_router = Router()

USER_LEVELS = ["Новичок", "Любитель", "Профи"]


def _configure_yookassa() -> bool:
    if not YOOKASSA_SHOP_ID or not YOOKASSA_API_KEY:
        return False
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_API_KEY
    return True


def _format_event_datetime(value):
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


@event_join_router.callback_query(F.data.startswith("join_"))
async def join_event(callback_query: types.CallbackQuery, bot: Bot):
    await callback_query.message.edit_reply_markup(reply_markup=None)

    try:
        event_id = int(callback_query.data.split("join_")[1])
    except (IndexError, ValueError):
        await callback_query.message.answer("Ошибка: неверный формат данных события.")
        return

    user_id = callback_query.from_user.id

    with get_db() as db:
        event = db.query(Event).filter_by(id=event_id).first()
        if not event:
            await callback_query.message.answer("Событие не найдено.")
            return

        user = db.query(User).filter_by(id=user_id).first()
        if not user or not user.is_registered:
            await callback_query.message.answer(
                "Чтобы записаться на игру, сначала завершите регистрацию.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="Пройти регистрацию", callback_data="start_reg")]]
                )
            )
            return

        if event.current_participants >= event.max_participants:
            await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
            return

        existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        if existing_registration:
            if existing_registration.is_paid:
                await callback_query.message.answer(
                    f"Вы уже записаны на событие <b>{html.escape(event.name or '')}</b>.",
                    parse_mode="HTML"
                )
            else:
                await callback_query.message.answer(
                    "У вас есть незавершённая оплата по этому событию. Проверьте статус платежа."
                )
            return

        user_level = user.user_level or "Новичок"
        event_level = event.players_level or "Смешанный"

        if event_level == "Любители и профи" and user_level == "Новичок":
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="events_list")]]
            )
            await callback_query.message.answer(
                "⚠️ Ваш уровень: <b>Новичок</b>.\n"
                "Это событие только для <b>Любителей и Профи</b>.",
                reply_markup=markup,
                parse_mode="HTML"
            )
            await callback_query.answer()
            return

        if event.price == 0:
            new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
            db.add(new_registration)
            event.current_participants += 1
            user.user_games += 1

            await callback_query.message.answer(
                f"✅ Вы успешно записаны на событие <b>{html.escape(event.name or '')}</b>.\n"
                f"📅 Дата: <b>{_format_event_datetime(event.event_time)}</b>\n"
                f"📍 Адрес: <b>{html.escape(event.address or '-')}</b>\n"
                f"👥 Участников: <b>{event.current_participants}/{event.max_participants}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
                ]]),
                parse_mode="HTML"
            )
            return

    if not _configure_yookassa():
        await callback_query.message.answer(
            "Сейчас недоступна онлайн-оплата. Напишите администратору, и мы поможем завершить запись."
        )
        return

    try:
        payment = Payment.create({
            "amount": {"value": str(event.price), "currency": "RUB"},
            "payment_method_data": {"type": "sbp"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
            "capture": True,
            "description": f"Оплата участия в событии {event.name}",
            "metadata": {"user_id": user_id, "event_id": event_id},
        })

        confirmation_url = payment.confirmation.confirmation_url
        pay_btn = InlineKeyboardButton(text="💳 Оплатить", url=confirmation_url)
        markup = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])

        await callback_query.message.answer(
            f"Для записи на <b>{html.escape(event.name or '')}</b> оплатите участие по кнопке ниже.\n"
            f"💰 Стоимость: <b>{event.price} руб.</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )

        await check_payment(payment.id, event_id, user_id, callback_query, bot)
    except Exception as e:
        logger.exception("Ошибка при создании платежа: %s", e)
        await callback_query.message.answer("Ошибка при создании платежа. Попробуйте позже.")


async def check_payment(payment_id, event_id, user_id, callback: types.CallbackQuery, bot: Bot):
    try:
        for _ in range(10):
            await asyncio.sleep(20)
            payment = Payment.find_one(payment_id)
            if payment.status == "succeeded":
                with get_db() as db:
                    event = db.query(Event).filter_by(id=event_id).first()
                    user = db.query(User).filter_by(id=user_id).first()

                    if not event or not user:
                        return

                    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
                    if existing_registration:
                        if not existing_registration.is_paid:
                            existing_registration.is_paid = True
                            event.current_participants += 1
                            user.user_games += 1
                    else:
                        new_registration = Registration(user_id=user_id, event_id=event_id, is_paid=True)
                        db.add(new_registration)
                        event.current_participants += 1
                        user.user_games += 1

                    payer_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    receipt_info = (
                        "📄 Квитанция об оплате\n"
                        f"🎉 Событие: {html.escape(event.name or '')}\n"
                        f"📅 Дата и время: {_format_event_datetime(event.event_time)}\n"
                        f"📍 Адрес: {html.escape(event.address or '-')}\n"
                        f"🆔 ID участника: <code>{user.id}</code>\n"
                        f"👤 Участник: {html.escape(payer_name or 'Без имени')}\n"
                        f"📞 Телефон: {html.escape(user.phone_number or '-')}\n"
                        f"💰 Сумма: {event.price} руб."
                    )

                    if ADMIN:
                        await bot.send_message(ADMIN, receipt_info, parse_mode="HTML")
                    if ADMIN_2:
                        await bot.send_message(ADMIN_2, receipt_info, parse_mode="HTML")

                    await callback.message.answer(
                        f"✅ Оплата прошла успешно.\n"
                        f"Вы записаны на событие <b>{html.escape(event.name or '')}</b>.\n"
                        f"📅 Дата: <b>{_format_event_datetime(event.event_time)}</b>",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
                        ]]),
                        parse_mode="HTML"
                    )
                return

            if payment.status in ["canceled", "expired"]:
                await callback.message.answer("Оплата была отменена или срок действия платежа истёк.")
                return

        await callback.message.answer("Платёж ещё обрабатывается. Проверьте статус чуть позже.")
    except Exception as e:
        logger.error("Ошибка проверки платежа: %s", e)


@event_join_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    with get_db() as db:
        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if not registration or not event:
            await callback_query.answer("Вы не были записаны на это событие.")
            return

        user_name = f"{html.escape(registration.user.first_name or '')} {html.escape(registration.user.last_name or '')}".strip()
        if ADMIN:
            await callback_query.bot.send_message(
                ADMIN,
                f"Пользователь {user_name} отменил регистрацию на событие {html.escape(event.name or '')}",
                parse_mode="HTML"
            )

        db.delete(registration)
        event.current_participants -= 1
        if event.current_participants < 0:
            event.current_participants = 0

    await callback_query.message.answer("Вы успешно отменили регистрацию на это событие.")


@event_join_router.callback_query(F.data.startswith("force_join_"))
async def force_join(callback: types.CallbackQuery, bot: Bot):
    event_id = int(callback.data.split("_")[-1])

    with get_db() as db:
        user = db.query(User).filter_by(id=callback.from_user.id).first()
        event = db.query(Event).filter_by(id=event_id).first()

    if not user or not event:
        await callback.message.answer("Пользователь или событие не найдены.")
        return

    if not _configure_yookassa():
        await callback.message.answer("Сервис онлайн-оплаты недоступен.")
        return

    try:
        payment = Payment.create({
            "amount": {"value": str(event.price), "currency": "RUB"},
            "payment_method_data": {"type": "sbp"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
            "capture": True,
            "description": f"Оплата участия в событии {event.name}",
            "metadata": {"user_id": user.id, "event_id": event_id},
        })
        confirmation_url = payment.confirmation.confirmation_url
        pay_btn = InlineKeyboardButton(text="💳 Оплатить", url=confirmation_url)
        markup = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])

        await callback.message.answer(
            "Оплатите участие, нажав кнопку ниже:",
            reply_markup=markup
        )
        await check_payment(payment.id, event_id, user.id, callback, bot)
    except Exception as e:
        logger.exception("Ошибка при создании платежа: %s", e)
        await callback.message.answer("Ошибка при создании платежа. Попробуйте позже.")


@event_join_router.callback_query(F.data == "cancel_join")
async def cancel_join(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="main_menu")
    await callback.message.answer(
        "❌ Запись отменена. Вы всегда можете выбрать другое событие!",
        reply_markup=builder.as_markup()
    )
