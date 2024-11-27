import logging
import os
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Registration, Event
from handlers.reminder import ReminderCallback
from yookassa import Payment, Configuration
from dotenv import load_dotenv
import uuid

load_dotenv()
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

event_join_router = Router()


@event_join_router.callback_query(F.data.startswith("join_"))
async def join_event(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    try:
        event_id = int(callback_query.data.split("join_")[1])
    except (IndexError, ValueError):
        await callback_query.message.answer("Ошибка: неверный формат данных события.")
        return

    user_id = callback_query.from_user.id
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        await callback_query.message.answer("Событие не найдено")
        return

    # проверка количества мест
    if event.current_participants >= event.max_participants:
        await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
        return

    # Проверка, что пользователь уже не записан на это событие
    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    if existing_registration and existing_registration.is_paid:
        await callback_query.message.answer("Вы уже записаны на это событие.")
        return

    # Проверка на бесплатное событие
    if event.price == 0:
        new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
        event.current_participants += 1
        db.add(new_registration)
        db.commit()

        await callback_query.message.answer(
            f"Вы успешно зарегистрированы на бесплатное событие: {event.name}."
        )
        return

    id_key = uuid.uuid4()

    try:
        payment = Payment.create({
            "amount": {
                "value": str(event.price),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/quanyshkz_bot/"  # Укажите URL возврата
            },
            "capture": True,
            "description": f"Оплата участия в событии {event.name}",
            "metadata": {
                "user_id": user_id,
                "event_id": event_id
            },
            "receipt": {
                "customer": {
                    "full_name": callback_query.from_user.full_name or "Имя не указано",
                    "email": "example@example.com"  # Замените на реальный email пользователя
                },
                "items": [
                    {
                        "description": f"Участие в событии {event.name}",
                        "quantity": "1.00",
                        "amount": {
                            "value": str(event.price),
                            "currency": "RUB"
                        },
                        "vat_code": "1",  # Подтвердите правильность кода НДС у ЮKassa
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            },
            "refundable": False,
            "test": True  # Указание на тестовый режим платежа
        }, id_key)
        check_btn = InlineKeyboardButton(text="Проверить оплату",
                                         callback_data=f"check_{payment.id}_{event.id}")
        markup = InlineKeyboardMarkup(inline_keyboard=[[check_btn]])
        confirmation_url = payment.confirmation.confirmation_url
        await callback_query.message.answer(
            f"Для завершения тестовой оплаты перейдите по ссылке: {confirmation_url}", reply_markup=markup
        )

    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при создании платежа. Попробуйте позже.")
        logging.error(f"Ошибка при создании тестового платежа: {e}")


@event_join_router.callback_query(F.data.startswith("check_"))
async def check_payment(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    payment_id, event_id = data[1], int(data[2])
    user_id = callback_query.from_user.id

    # Проверяем статус платежа
    try:
        payment = Payment.find_one(payment_id)
        if payment.status == "succeeded":
            # Регистрируем пользователя на событие
            db = next(get_db())
            event = db.query(Event).filter_by(id=event_id).first()
            new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
            db.add(new_registration)
            event.current_participants += 1
            db.commit()
            main_menu_btn = types.KeyboardButton(text="/main_menu")
            keyboard = types.ReplyKeyboardMarkup(keyboard=[[main_menu_btn]], resize_keyboard=True)
            await callback_query.message.answer("Оплата прошла успешно! Вы зарегистрированы на событие.",
                                                reply_markup=keyboard)
        elif payment.status == "pending":
            await callback_query.message.answer("Оплата еще не завершена. Пожалуйста, завершите платеж.")
        else:
            await callback_query.message.answer("Оплата не прошла. Попробуйте снова.")
    except Exception as e:
        await callback_query.message.answer("Ошибка при проверке платежа. Попробуйте позже.")
        print(f"Ошибка при проверке платежа: {e}")
