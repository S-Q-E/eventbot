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

USER_LEVELS = ["РќРѕРІРёС‡РѕРє", "Р›СЋР±РёС‚РµР»СЊ", "РџСЂРѕС„Рё"]


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
        await callback_query.message.answer("РћС€РёР±РєР°: РЅРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РґР°РЅРЅС‹С… СЃРѕР±С‹С‚РёСЏ.")
        return

    user_id = callback_query.from_user.id

    event_name = ""
    event_price = 0

    with get_db() as db:
        event = db.query(Event).filter_by(id=event_id).first()
        if not event:
            await callback_query.message.answer("РЎРѕР±С‹С‚РёРµ РЅРµ РЅР°Р№РґРµРЅРѕ.")
            return
        event_name = event.name or ""
        event_price = event.price or 0

        user = db.query(User).filter_by(id=user_id).first()
        if not user or not user.is_registered:
            await callback_query.message.answer(
                "Р§С‚РѕР±С‹ Р·Р°РїРёСЃР°С‚СЊСЃСЏ РЅР° РёРіСЂСѓ, СЃРЅР°С‡Р°Р»Р° Р·Р°РІРµСЂС€РёС‚Рµ СЂРµРіРёСЃС‚СЂР°С†РёСЋ.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="РџСЂРѕР№С‚Рё СЂРµРіРёСЃС‚СЂР°С†РёСЋ", callback_data="start_reg")]]
                )
            )
            return

        if event.current_participants >= event.max_participants:
            await callback_query.message.answer("Р’СЃРµ РјРµСЃС‚Р° Р·Р°РЅСЏС‚С‹. Р‘СѓРґРµРј Р¶РґР°С‚СЊ РІР°СЃ РІ СЃР»РµРґСѓСЋС‰РёР№ СЂР°Р·!")
            return

        existing_registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        if existing_registration:
            if existing_registration.is_paid:
                await callback_query.message.answer(
                    f"Р’С‹ СѓР¶Рµ Р·Р°РїРёСЃР°РЅС‹ РЅР° СЃРѕР±С‹С‚РёРµ <b>{html.escape(event.name or '')}</b>.",
                    parse_mode="HTML"
                )
            else:
                await callback_query.message.answer(
                    "РЈ РІР°СЃ РµСЃС‚СЊ РЅРµР·Р°РІРµСЂС€С‘РЅРЅР°СЏ РѕРїР»Р°С‚Р° РїРѕ СЌС‚РѕРјСѓ СЃРѕР±С‹С‚РёСЋ. РџСЂРѕРІРµСЂСЊС‚Рµ СЃС‚Р°С‚СѓСЃ РїР»Р°С‚РµР¶Р°."
                )
            return

        user_level = user.user_level or "РќРѕРІРёС‡РѕРє"
        event_level = event.players_level or "РЎРјРµС€Р°РЅРЅС‹Р№"

        if event_level == "Р›СЋР±РёС‚РµР»Рё Рё РїСЂРѕС„Рё" and user_level == "РќРѕРІРёС‡РѕРє":
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="РќР°Р·Р°Рґ", callback_data="events_list")]]
            )
            await callback_query.message.answer(
                "вљ пёЏ Р’Р°С€ СѓСЂРѕРІРµРЅСЊ: <b>РќРѕРІРёС‡РѕРє</b>.\n"
                "Р­С‚Рѕ СЃРѕР±С‹С‚РёРµ С‚РѕР»СЊРєРѕ РґР»СЏ <b>Р›СЋР±РёС‚РµР»РµР№ Рё РџСЂРѕС„Рё</b>.",
                reply_markup=markup,
                parse_mode="HTML"
            )
            await callback_query.answer()
            return

        if event_price == 0:
            new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
            db.add(new_registration)
            event.current_participants += 1
            user.user_games += 1

            await callback_query.message.answer(
                f"вњ… Р’С‹ СѓСЃРїРµС€РЅРѕ Р·Р°РїРёСЃР°РЅС‹ РЅР° СЃРѕР±С‹С‚РёРµ <b>{html.escape(event.name or '')}</b>.\n"
                f"рџ“… Р”Р°С‚Р°: <b>{_format_event_datetime(event.event_time)}</b>\n"
                f"рџ“Ќ РђРґСЂРµСЃ: <b>{html.escape(event.address or '-')}</b>\n"
                f"рџ‘Ґ РЈС‡Р°СЃС‚РЅРёРєРѕРІ: <b>{event.current_participants}/{event.max_participants}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ", callback_data="main_menu")
                ]]),
                parse_mode="HTML"
            )
            return

    if not _configure_yookassa():
        await callback_query.message.answer(
            "РЎРµР№С‡Р°СЃ РЅРµРґРѕСЃС‚СѓРїРЅР° РѕРЅР»Р°Р№РЅ-РѕРїР»Р°С‚Р°. РќР°РїРёС€РёС‚Рµ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ, Рё РјС‹ РїРѕРјРѕР¶РµРј Р·Р°РІРµСЂС€РёС‚СЊ Р·Р°РїРёСЃСЊ."
        )
        return

    try:
        payment = Payment.create({
            "amount": {"value": str(event_price), "currency": "RUB"},
            "payment_method_data": {"type": "sbp"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
            "capture": True,
            "description": f"РћРїР»Р°С‚Р° СѓС‡Р°СЃС‚РёСЏ РІ СЃРѕР±С‹С‚РёРё {event_name}",
            "metadata": {"user_id": user_id, "event_id": event_id},
        })

        confirmation_url = payment.confirmation.confirmation_url
        pay_btn = InlineKeyboardButton(text="рџ’і РћРїР»Р°С‚РёС‚СЊ", url=confirmation_url)
        markup = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])

        await callback_query.message.answer(
            f"Р”Р»СЏ Р·Р°РїРёСЃРё РЅР° <b>{html.escape(event_name)}</b> РѕРїР»Р°С‚РёС‚Рµ СѓС‡Р°СЃС‚РёРµ РїРѕ РєРЅРѕРїРєРµ РЅРёР¶Рµ.\n"
            f"рџ’° РЎС‚РѕРёРјРѕСЃС‚СЊ: <b>{event_price} СЂСѓР±.</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )

        await check_payment(payment.id, event_id, user_id, callback_query, bot)
    except Exception as e:
        logger.exception("РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё РїР»Р°С‚РµР¶Р°: %s", e)
        await callback_query.message.answer("РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё РїР»Р°С‚РµР¶Р°. РџРѕРїСЂРѕР±СѓР№С‚Рµ РїРѕР·Р¶Рµ.")


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
                        "рџ“„ РљРІРёС‚Р°РЅС†РёСЏ РѕР± РѕРїР»Р°С‚Рµ\n"
                        f"рџЋ‰ РЎРѕР±С‹С‚РёРµ: {html.escape(event.name or '')}\n"
                        f"рџ“… Р”Р°С‚Р° Рё РІСЂРµРјСЏ: {_format_event_datetime(event.event_time)}\n"
                        f"рџ“Ќ РђРґСЂРµСЃ: {html.escape(event.address or '-')}\n"
                        f"рџ†” ID СѓС‡Р°СЃС‚РЅРёРєР°: <code>{user.id}</code>\n"
                        f"рџ‘¤ РЈС‡Р°СЃС‚РЅРёРє: {html.escape(payer_name or 'Р‘РµР· РёРјРµРЅРё')}\n"
                        f"рџ“ћ РўРµР»РµС„РѕРЅ: {html.escape(user.phone_number or '-')}\n"
                        f"рџ’° РЎСѓРјРјР°: {event.price} СЂСѓР±."
                    )

                    if ADMIN:
                        await bot.send_message(ADMIN, receipt_info, parse_mode="HTML")
                    if ADMIN_2:
                        await bot.send_message(ADMIN_2, receipt_info, parse_mode="HTML")

                    await callback.message.answer(
                        f"вњ… РћРїР»Р°С‚Р° РїСЂРѕС€Р»Р° СѓСЃРїРµС€РЅРѕ.\n"
                        f"Р’С‹ Р·Р°РїРёСЃР°РЅС‹ РЅР° СЃРѕР±С‹С‚РёРµ <b>{html.escape(event.name or '')}</b>.\n"
                        f"рџ“… Р”Р°С‚Р°: <b>{_format_event_datetime(event.event_time)}</b>",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text="Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ", callback_data="main_menu")
                        ]]),
                        parse_mode="HTML"
                    )
                return

            if payment.status in ["canceled", "expired"]:
                await callback.message.answer("РћРїР»Р°С‚Р° Р±С‹Р»Р° РѕС‚РјРµРЅРµРЅР° РёР»Рё СЃСЂРѕРє РґРµР№СЃС‚РІРёСЏ РїР»Р°С‚РµР¶Р° РёСЃС‚С‘Рє.")
                return

        await callback.message.answer("РџР»Р°С‚С‘Р¶ РµС‰С‘ РѕР±СЂР°Р±Р°С‚С‹РІР°РµС‚СЃСЏ. РџСЂРѕРІРµСЂСЊС‚Рµ СЃС‚Р°С‚СѓСЃ С‡СѓС‚СЊ РїРѕР·Р¶Рµ.")
    except Exception as e:
        logger.error("РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё РїР»Р°С‚РµР¶Р°: %s", e)


@event_join_router.callback_query(F.data.startswith("cancel_registration_"))
async def cancel_registration(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[-1])
    user_id = callback_query.from_user.id

    with get_db() as db:
        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if not registration or not event:
            await callback_query.answer("Р’С‹ РЅРµ Р±С‹Р»Рё Р·Р°РїРёСЃР°РЅС‹ РЅР° СЌС‚Рѕ СЃРѕР±С‹С‚РёРµ.")
            return

        user_name = f"{html.escape(registration.user.first_name or '')} {html.escape(registration.user.last_name or '')}".strip()
        if ADMIN:
            await callback_query.bot.send_message(
                ADMIN,
                f"РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ {user_name} РѕС‚РјРµРЅРёР» СЂРµРіРёСЃС‚СЂР°С†РёСЋ РЅР° СЃРѕР±С‹С‚РёРµ {html.escape(event.name or '')}",
                parse_mode="HTML"
            )

        db.delete(registration)
        event.current_participants -= 1
        if event.current_participants < 0:
            event.current_participants = 0

    await callback_query.message.answer("Р’С‹ СѓСЃРїРµС€РЅРѕ РѕС‚РјРµРЅРёР»Рё СЂРµРіРёСЃС‚СЂР°С†РёСЋ РЅР° СЌС‚Рѕ СЃРѕР±С‹С‚РёРµ.")


@event_join_router.callback_query(F.data.startswith("force_join_"))
async def force_join(callback: types.CallbackQuery, bot: Bot):
    event_id = int(callback.data.split("_")[-1])

    with get_db() as db:
        user = db.query(User).filter_by(id=callback.from_user.id).first()
        event = db.query(Event).filter_by(id=event_id).first()

    if not user or not event:
        await callback.message.answer("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РёР»Рё СЃРѕР±С‹С‚РёРµ РЅРµ РЅР°Р№РґРµРЅС‹.")
        return

    if not _configure_yookassa():
        await callback.message.answer("РЎРµСЂРІРёСЃ РѕРЅР»Р°Р№РЅ-РѕРїР»Р°С‚С‹ РЅРµРґРѕСЃС‚СѓРїРµРЅ.")
        return

    try:
        payment = Payment.create({
            "amount": {"value": str(event.price), "currency": "RUB"},
            "payment_method_data": {"type": "sbp"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/GuruEvent_bot/"},
            "capture": True,
            "description": f"РћРїР»Р°С‚Р° СѓС‡Р°СЃС‚РёСЏ РІ СЃРѕР±С‹С‚РёРё {event.name}",
            "metadata": {"user_id": user.id, "event_id": event_id},
        })
        confirmation_url = payment.confirmation.confirmation_url
        pay_btn = InlineKeyboardButton(text="рџ’і РћРїР»Р°С‚РёС‚СЊ", url=confirmation_url)
        markup = InlineKeyboardMarkup(inline_keyboard=[[pay_btn]])

        await callback.message.answer(
            "РћРїР»Р°С‚РёС‚Рµ СѓС‡Р°СЃС‚РёРµ, РЅР°Р¶Р°РІ РєРЅРѕРїРєСѓ РЅРёР¶Рµ:",
            reply_markup=markup
        )
        await check_payment(payment.id, event_id, user.id, callback, bot)
    except Exception as e:
        logger.exception("РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё РїР»Р°С‚РµР¶Р°: %s", e)
        await callback.message.answer("РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё РїР»Р°С‚РµР¶Р°. РџРѕРїСЂРѕР±СѓР№С‚Рµ РїРѕР·Р¶Рµ.")


@event_join_router.callback_query(F.data == "cancel_join")
async def cancel_join(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="РќР°Р·Р°Рґ", callback_data="main_menu")
    await callback.message.answer(
        "вќЊ Р—Р°РїРёСЃСЊ РѕС‚РјРµРЅРµРЅР°. Р’С‹ РІСЃРµРіРґР° РјРѕР¶РµС‚Рµ РІС‹Р±СЂР°С‚СЊ РґСЂСѓРіРѕРµ СЃРѕР±С‹С‚РёРµ!",
        reply_markup=builder.as_markup()
    )
