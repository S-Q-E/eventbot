import asyncio
import logging
import os
import uuid
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


async def fetch_event(event_id):
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    return event, db

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
    event, db = await fetch_event(event_id)

    try:
        if not event:
            await callback_query.message.answer("Событие не найдено.")
            return

        if event.current_participants >= event.max_participants:
            await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
            return

        existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        if existing_registration:
            if existing_registration.is_paid:
                await callback_query.message.answer(f"Вы уже записаны на это событие {event.name}")
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
                reply_markup=markup
            )
            await callback_query.answer()
            return

        if event.price == 0:
            try:
                new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
                event.current_participants += 1
                db.add(new_registration)
                db.commit()

                await callback_query.message.answer(
                    f"Вы успешно зарегистрированы на бесплатное событие: <b>{event.name}</b>.\n\n",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
                    ]])
                )
            except Exception as e:
                db.rollback()
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
                reply_markup=markup
            )
            # Передаем payment_id в check_payment, чтобы отслеживать статус
            await check_payment(payment.id, event_id, user_id, callback_query, bot)

        except Exception as e:
            logger.exception(f"Ошибка при создании платежа. {e}")
            await callback_query.message.answer("Ошибка при создании платежа. Попробуйте позже.")
    finally:
        db.close()

import html

async def check_payment(payment_id, event_id, user_id, callback: types.CallbackQuery, bot: Bot):
    # Вместо бесконечного цикла будем проверять статус платежа ограниченное число раз
    # В идеале здесь должен быть Webhook, но для фикса заменим на короткий опрос
    try:
        for _ in range(5): # Проверяем 5 раз с паузой
            await asyncio.sleep(10)
            payment = Payment.find_one(payment_id)
            if payment.status == "succeeded":
                with get_db() as db:
                    event = db.query(Event).filter_by(id=event_id).first()
                    user = db.query(User).filter_by(id=user_id).first()
                    # ... (логика регистрации)
                return
        await callback.message.answer("Платеж еще обрабатывается. Вы получите уведомление после подтверждения.")
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")


@event_join_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    """
    Обрабатывает отмену регистрации на событие.
    """
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id
    with next(get_db()) as db:

        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if registration:
            await callback_query.bot.send_message(ADMIN, f"Пользователь {registration.user.first_name}"
                                                         f"{registration.user.last_name}"
                                                         f"отменил регистрацию на событие {event.name}")
            db.delete(registration)
            event.current_participants -= 1
            if event.current_participants < 0:
                event.current_participants = 0

            db.commit()
            await callback_query.message.answer("Вы успешно отменили регистрацию на это событие.")
            db.close()
        else:
            await callback_query.answer("Вы не были записаны на это событие.")


@event_join_router.callback_query(F.data.startswith("force_join_"))
async def force_join(callback: types.CallbackQuery, bot: Bot):
    event_id = int(callback.data.split("_")[-1])
    db = next(get_db())
    try:
        user = db.query(User).filter_by(id=callback.from_user.id).first()
        event = db.query(Event).filter_by(id=event_id).first()
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
                reply_markup=markup
            )
            await check_payment(payment.id, event_id, user.id, callback, bot)
        except Exception as e:
            logger.exception(f"Ошибка при создании платежа. {e}")
            await callback.message.answer("Ошибка при создании платежа. Попробуйте позже.")
    except Exception as e:
        await callback.message.answer("Ошибка при записи на игру")
    finally:
        db.close()


@event_join_router.callback_query(F.data == "cancel_join")
async def cancel_join(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="main_menu")
    await callback.message.answer("❌ Запись отменена. Вы всегда можете выбрать другое событие!", reply_markup=builder.as_markup())
