import asyncio
import logging
import os
import uuid
from aiogram import Router, types, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, Registration, Event, User
from yookassa import Payment, Configuration
from dotenv import load_dotenv
from keyboards.notif_keyboard import get_notification_keyboard
from utils.notify_user import notify_all_users_event_full

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

    if not event:
        await callback_query.message.answer("Событие не найдено.")
        return

    if event.current_participants == event.max_participants:
        await callback_query.message.answer("Все места заняты. Будем ждать вас в следующий раз!")
        return

    existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
    if existing_registration:
        logging.debug(
            f"Пользователь {user_id} уже зарегистрирован на событие {event_id}. Оплачен: {existing_registration.is_paid}")
        if existing_registration.is_paid:
            await callback_query.message.answer(f"Вы уже записаны на это событие {event.name}")
            return
        else:
            await callback_query.message.answer(f"Вы начали оплату, но не завершили ее. Проверьте статус платежа")
            return

    if event.price == 0:
        try:
            new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
            event.current_participants += 1
            logger.debug(f"Добавление новой регистрации для пользователя {user_id} на событие {event_id}.")
            db.add(new_registration)
            db.commit()
            await callback_query.message.answer(
                f"Вы успешно зарегистрированы на бесплатное событие: <b>{event.name}</b>.\n\n"
                f"Пожалуйста, выберите время напоминания.", reply_markup=get_notification_keyboard(event_id)
            )
        except Exception as e:
            logger.exception(f"Ошибка при регистрации на бесплатное событие. {e}")
            await callback_query.message.answer("Произошла ошибка. Попробуйте снова.")
        return

    try:
        payment = Payment.create({
            "amount": {"value": str(event.price), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
            "capture": True,
            "description": f"Оплата участия в событии {event.name}",
            "metadata": {"user_id": user_id, "event_id": event_id},
        })
        confirmation_url = payment.confirmation.confirmation_url
        pay_btn = InlineKeyboardButton(text="💳 Оплатить", url=confirmation_url)
        markup = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])
        await callback_query.message.answer(
            f"Оплатите участие, нажав на кнопку <code>Оплатить</code>, <b>выберите способ оплаты СБП:</b>\n", reply_markup=markup
        )
        await check_payment(payment.id, event_id, user_id, callback_query, bot)
    except Exception as e:
        logger.exception(f"Ошибка при создании платежа. {e}")
        await callback_query.message.answer("Ошибка при создании платежа. Попробуйте позже.")


async def check_payment(payment_id, event_id, user_id, callback: types.CallbackQuery, bot: Bot):
    db = next(get_db())
    try:
        intervals = [30, 60, 180, 600, 1800, 3600]
        for delay in intervals:
            payment = Payment.find_one(payment_id)
            if payment.status == "succeeded":
                event, db = await fetch_event(event_id)
                existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
                if existing_registration:
                    existing_registration.is_paid = True
                else:
                    new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
                    db.add(new_registration)
                    event.current_participants += 1
                db.commit()

                if event.current_participants == event.max_participants:
                    await notify_all_users_event_full(bot, event)
                user = db.query(User).filter(User.id == user_id).first()
                receipt_info = (
                    f"📄 Чек об оплате:\n"
                    f"🎊 Событие: {event.name}\n"
                    f"📆 Дата события: {event.event_time}\n"
                    f"🆔 Оплатил: {user.first_name}, {user.last_name}\n"
                    f"💰 Сумма: {event.price} руб.\n"
                    f"🛠 Способ оплаты: {payment.payment_method.type}\n"
                    f"👤 Номер плательщика: {user.phone_number}\n"
                    f"🕒 Дата создания: {payment.created_at}\n"
                )
                await callback.bot.send_message(ADMIN, receipt_info)
                await callback.bot.send_message(ADMIN_2, receipt_info)
                logging.info(
                    f"Оплата {payment_id} на событие {event.name} - оплатил {user.first_name} {user.last_name}\n")
                await callback.message.answer(f"Оплата прошла успешно! Вы зарегистрированы на событие <b>{event.name}</b>.\n"
                                              f"Выберите время напоминания.", reply_markup=get_notification_keyboard(event_id)
                )
                return
            elif payment.status in ["pending", "waiting_for_capture"]:
                await callback.message.answer("Платеж обрабатывается. Пожалуйста подождите")
                await asyncio.sleep(delay)
            else:
                await callback.message.answer("Вы не оплатили событие. Регистрация отменена")
                break
        await callback.message.answer("Оплата не завершена. Попробуйте снова.")
    except Exception as e:
        logger.exception(f"Ошибка при проверке статуса платежа. {e}")
        await callback.message.answer("Ошибка при проверке платежа. Попробуйте позже.")
    finally:
        db.close()
