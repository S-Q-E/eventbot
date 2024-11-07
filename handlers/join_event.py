import logging
import os
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Registration, Event
# from handlers.reminder import ReminderCallback
from yookassa import Payment, Configuration
from dotenv import load_dotenv
import uuid

load_dotenv()
YOOKASSA_SHOP_ID = os.getenv("TEST_SHOP")
YOOKASSA_API_KEY = os.getenv("TEST_KEY")

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

    if event.current_participants >= event.max_participants:
        await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
        return

    # Проверка, что пользователь уже не записан на это событие
    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    if existing_registration and existing_registration.is_paid:
        await callback_query.message.answer("Вы уже записаны на это событие.")
        return
    try:
        payment = Payment.create({
            "amount": {
                "value": str(event.price),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/quanyshkz_bot/payment_success"  # Укажите URL возврата
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
            "test": True  # Указание на тестовый режим платежа
        })  # Уникальный ключ идемпотентности

        confirmation_url = payment.confirmation.confirmation_url
        await callback_query.message.answer(
            f"Для завершения тестовой оплаты перейдите по ссылке: {confirmation_url}"
        )

    except Exception as e:
        await callback_query.message.answer("Произошла ошибка при создании платежа. Попробуйте позже.")
        logging.error(f"Ошибка при создании тестового платежа: {e}")



# @event_join_router.("/webhook/yookassa")
# async def yookassa_webhook(request: types.Request):
#     data = await request.json()
#     try:
#         if data['event'] == 'payment.succeeded':
#             metadata = data['object']['metadata']
#             user_id = metadata.get('user_id')
#             event_id = metadata.get('event_id')
#
#             db = next(get_db())
#             # Обновляем регистрацию пользователя после успешной оплаты
#             registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
#             if registration:
#                 registration.is_paid = True
#                 # Обновляем счетчик участников
#                 event = db.query(Event).filter_by(id=event_id).first()
#                 if event:
#                     event.current_participants += 1
#                 db.commit()
#
#                 # Уведомляем пользователя о завершении записи
#                 await bot.send_message(user_id, f"Оплата подтверждена, вы записаны на событие {event.name}!")
#
#     except Exception as e:
#         logging.error(f"Ошибка при обработке вебхука Юкассы: {e}")
#
#     return {"status": "ok"}
