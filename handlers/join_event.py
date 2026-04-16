import asyncio
import logging
import os
import uuid
import html
from aiogram import Router, types, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import get_db, Registration, Event, User
from yookassa import Payment, Configuration
from dotenv import load_dotenv

load_dotenv()
ADMIN = os.getenv("ADMIN_2")
ADMIN_2 = os.getenv("ADMIN_3")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")

if not YOOKASSA_SHOP_ID or not YOOKASSA_API_KEY:
    raise ValueError("Yookassa credentials are not set. Please check your .env file.")

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

logger = logging.getLogger(__name__)
event_join_router = Router()


USER_LEVELS = ["Новичок", "Любитель", "Профи"]


def get_level_index(level):
    try:
        return USER_LEVELS.index(level)
    except (ValueError, TypeError):
        return -1  # Если уровень не установлен


@event_join_router.callback_query(F.data.startswith("join_"))
async def join_event(callback_query: types.CallbackQuery, bot: Bot):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    try:
        event_id = int(callback_query.data.split("join_")[1])
    except (IndexError, ValueError):
        await callback_query.message.answer("Ошибка: неверный формат данных события.")
        return

    user_id = callback_query.from_user.id
    
    try:
        with get_db() as db:
            event = db.query(Event).filter_by(id=event_id).first()
            if not event:
                await callback_query.message.answer("Событие не найдено.")
                return

            if event.current_participants >= event.max_participants:
                await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
                return

            existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
            if existing_registration:
                if existing_registration.is_paid:
                    await callback_query.message.answer(f"Вы уже записаны на это событие {html.escape(event.name)}", parse_mode="HTML")
                    return
                else:
                    await callback_query.message.answer(f"Вы начали оплату, но не завершили ее. Проверьте статус платежа")
                    return

            user = db.query(User).filter_by(id=callback_query.from_user.id).first()
            user_level = user.user_level or "Новичок"
            event_level = event.players_level or "Смешанный"

            if event_level == "Любители и профи" and user_level == "Новичок":
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="❌ Назад", callback_data="events_list")]
                    ]
                )
                await callback_query.message.answer(
                    "⚠️ Ваш уровень: <b>Новичок</b>\n"
                    "А это событие только для <b>Любителей и Профи</b>!\n\n"
                    "Запись невозможна 🤔",
                    reply_markup=markup,
                    parse_mode="HTML"
                )
                await callback_query.answer()
                return

            if event.price == 0:
                try:
                    new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
                    event.current_participants += 1
                    db.add(new_registration)
                    # db.commit() is automatic

                    await callback_query.message.answer(
                        f"Вы успешно зарегистрированы на бесплатное событие: <b>{html.escape(event.name)}</b>.\n\n",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
                        ]]),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.exception(f"Ошибка при регистрации на бесплатное событие. {e}")
                    await callback_query.message.answer("Произошла ошибка. Попробуйте снова.")
                return

            # Создание платежа для платных событий
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
                    f"Оплатите участие, нажав на кнопку <code>Оплатить</code>, <b>выберите способ оплаты СБП:</b>\n",
                    reply_markup=markup,
                    parse_mode="HTML"
                )
                # Передаем payment_id в check_payment, чтобы отслеживать статус
                await check_payment(payment.id, event_id, user_id, callback_query, bot)

            except Exception as e:
                logger.exception(f"Ошибка при создании платежа. {e}")
                await callback_query.message.answer("Ошибка при создании платежа. Попробуйте позже.")
    except Exception as e:
        logger.exception(f"General error in join_event: {e}")
        await callback_query.message.answer("Произошла ошибка. Попробуйте позже.")


async def check_payment(payment_id, event_id, user_id, callback: types.CallbackQuery, bot: Bot):
    try:
        for _ in range(10): # Проверяем 10 раз с паузой 20 сек (около 3 минут)
            await asyncio.sleep(20)
            payment = Payment.find_one(payment_id)
            if payment.status == "succeeded":
                with get_db() as db:
                    event = db.query(Event).filter_by(id=event_id).first()
                    user = db.query(User).filter_by(id=user_id).first()
                    
                    if not event or not user:
                        return

                    # Проверяем, не зарегистрирован ли пользователь уже
                    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
                    if existing_registration:
                        if not existing_registration.is_paid:
                            existing_registration.is_paid = True
                            event.current_participants += 1
                    else:
                        new_registration = Registration(user_id=user_id, event_id=event_id, is_paid=True)
                        db.add(new_registration)
                        event.current_participants += 1

                    # db.commit() is automatic

                    receipt_info = (
                        f"📄 Чек об оплате:\n"
                        f"🎊 Событие: {html.escape(event.name)}\n"
                        f"📆 Дата события: {event.event_time}\n"
                        f"🆔 Оплатил: {html.escape(user.first_name or '')}, {html.escape(user.last_name or '')}\n"
                        f"💰 Сумма: {event.price} руб.\n"
                    )

                    await bot.send_message(ADMIN, receipt_info, parse_mode="HTML")
                    if ADMIN_2:
                        await bot.send_message(ADMIN_2, receipt_info, parse_mode="HTML")

                    await callback.message.answer(
                        f"Оплата прошла успешно! Вы зарегистрированы на событие <b>{html.escape(event.name)}</b>.\n",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
                        ]]),
                        parse_mode="HTML"
                    )
                return
            elif payment.status in ["canceled", "expired"]:
                await callback.message.answer("Оплата была отменена или срок действия платежа истек.")
                return
                
        await callback.message.answer("Платеж еще обрабатывается. Пожалуйста, проверьте статус позже в Личном кабинете.")
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")


@event_join_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    """
    Обрабатывает отмену регистрации на событие.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    with get_db() as db:

        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if registration:
            user_name = f"{html.escape(registration.user.first_name or '')} {html.escape(registration.user.last_name or '')}".strip()
            await callback_query.bot.send_message(ADMIN, f"Пользователь {user_name} отменил регистрацию на событие {html.escape(event.name)}", parse_mode="HTML")
            db.delete(registration)
            event.current_participants -= 1
            if event.current_participants < 0:
                event.current_participants = 0

            # db.commit() is automatic
            await callback_query.message.answer("Вы успешно отменили регистрацию на это событие.")
        else:
            await callback_query.answer("Вы не были записаны на это событие.")


@event_join_router.callback_query(F.data.startswith("force_join_"))
async def force_join(callback: types.CallbackQuery, bot: Bot):
    event_id = int(callback.data.split("_")[-1])
    try:
        with get_db() as db:
            user = db.query(User).filter_by(id=callback.from_user.id).first()
            event = db.query(Event).filter_by(id=event_id).first()
            if not event:
                await callback.message.answer("Событие не найдено.")
                return
            try:
                payment = Payment.create({
                    "amount": {"value": str(event.price), "currency": "RUB"},
                    "payment_method_data": {
                        "type": "sbp"
                    },
                    "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
                    "capture": True,
                    "description": f"Оплата участия в событии {event.name}",
                    "metadata": {"user_id": user.id, "event_id": event_id},
                })
                confirmation_url = payment.confirmation.confirmation_url
                pay_btn = InlineKeyboardButton(text="💳 Оплатить", url=confirmation_url)
                markup = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])
                await callback.message.answer(
                    f"Оплатите участие, нажав на кнопку <code>Оплатить</code>, <b>выберите способ оплаты СБП:</b>\n",
                    reply_markup=markup,
                    parse_mode="HTML"
                )
                await check_payment(payment.id, event_id, user.id, callback, bot)
            except Exception as e:
                logger.exception(f"Ошибка при создании платежа. {e}")
                await callback.message.answer("Ошибка при создании платежа. Попробуйте позже.")
    except Exception as e:
        logger.exception(f"Error in force_join: {e}")
        await callback.message.answer("Ошибка при записи на игру")


@event_join_router.callback_query(F.data == "cancel_join")
async def cancel_join(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="main_menu")
    await callback.message.answer("❌ Запись отменена. Вы всегда можете выбрать другое событие!", reply_markup=builder.as_markup())
