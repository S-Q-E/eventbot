import logging
import os
import uuid
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Registration, Event, User
from yookassa import Payment, Configuration
from dotenv import load_dotenv
from keyboards.notif_keyboard import get_notification_keyboard

load_dotenv()
ADMIN = os.getenv("ADMIN_2")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")

if not YOOKASSA_SHOP_ID or not YOOKASSA_API_KEY:
    raise ValueError("Yookassa credentials are not set. Please check your .env file.")

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

logger = logging.getLogger(__name__)
event_join_router = Router()


# Helper function to fetch the event from the database
async def fetch_event(event_id):
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    return event, db


@event_join_router.callback_query(F.data.startswith("join_"))
async def join_event(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    try:
        event_id = int(callback_query.data.split("join_")[1])
    except (IndexError, ValueError):
        await callback_query.message.answer("Ошибка: неверный формат данных события.")
        return

    user_id = callback_query.from_user.id
    event, db = await fetch_event(event_id)

    if not event:
        await callback_query.message.answer("Событие не найдено.")
        return

    # Check for available spots
    if event.current_participants >= event.max_participants:
        await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
        return

    # Prevent duplicate registration
    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    if existing_registration and existing_registration.is_paid:
        await callback_query.message.answer("Вы уже записаны на это событие.")
        return

    # Check if event is free
    if event.price == 0:
        try:
            new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
            event.current_participants += 1
            db.add(new_registration)
            db.commit()
            await callback_query.message.answer(
                f"Вы успешно зарегистрированы на бесплатное событие: <b>{event.name}</b>.\n\n"
                f"Пожалуйста, выберите время напоминания.", reply_markup=get_notification_keyboard(event_id)
            )
        except Exception as e:
            logger.exception("Ошибка при регистрации на бесплатное событие.")
            await callback_query.message.answer("Произошла ошибка. Попробуйте снова.")
        return

    # Handle paid event registration
    try:
        payment = Payment.create({
            "amount": {"value": str(event.price), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/your_bot/"},
            "capture": True,
            "description": f"Оплата участия в событии {event.name}",
            "metadata": {"user_id": user_id, "event_id": event_id},
        })

        confirmation_url = payment.confirmation.confirmation_url
        check_btn = InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_{payment.id}_{event.id}")
        markup = InlineKeyboardMarkup(inline_keyboard=[[check_btn]])

        await callback_query.message.answer(
            f"Оплатите участие, перейдя по ссылке: {confirmation_url}", reply_markup=markup
        )
    except Exception as e:
        logger.exception("Ошибка при создании платежа.")
        await callback_query.message.answer("Ошибка при создании платежа. Попробуйте позже.")


@event_join_router.callback_query(F.data.startswith("check_"))
async def check_payment(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    payment_id, event_id = data[1], int(data[2])
    user_id = callback_query.from_user.id

    try:
        payment = Payment.find_one(payment_id)
        if payment.status == "succeeded":
            event, db = await fetch_event(event_id)
            new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
            event.current_participants += 1
            db.add(new_registration)
            db.commit()
            user = db.query(User).filter(User.id == user_id).first()

            receipt_info = (
                f"📄 Чек об оплате:\n"
                f"🎊 Событие: {event.name}"
                f"🆔 Оплатил: {user.first_name}, {user.last_name}\n"
                f"💰 Сумма: {event.price}\n"
                f"🛠 Способ оплаты: {payment.payment_method.type}\n"
                f"👤 Номер плательщика: {user.phone_number}\n"
                f"🕒 Дата создания: {payment.created_at}\n"
            )
            await callback_query.bot.send_message(ADMIN, receipt_info)
            await callback_query.message.answer(
                f"Оплата прошла успешно! Вы зарегистрированы на событие <b>{event.name}</b>.\n"
                f"Выберите время напоминания.", reply_markup=get_notification_keyboard(event_id)
            )
        elif payment.status == "pending":
            await callback_query.message.answer("Оплата еще не завершена. Пожалуйста, завершите платеж.")
        else:
            await callback_query.message.answer("Оплата не прошла. Попробуйте снова.")
    except Exception as e:
        logger.exception(f"Ошибка при проверке статуса платежа. {e}")
        await callback_query.message.answer("Ошибка при проверке платежа. Попробуйте позже.")
