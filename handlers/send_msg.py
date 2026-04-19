import logging
import html
from datetime import datetime

from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import get_db, User, Registration, Category, Event

logger = logging.getLogger(__name__)
message_router = Router()


class AdminBroadcast(StatesGroup):
    waiting_for_text = State()
    waiting_for_text_confirm = State()
    waiting_for_photo = State()
    waiting_for_send_choice = State()
    waiting_for_category = State()


@message_router.callback_query(F.data == "send_to_users")
async def cmd_broadcast_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup()
    await cb.message.answer("Р’РІРµРґРёС‚Рµ С‚РµРєСЃС‚ СЂР°СЃСЃС‹Р»РєРё:")
    await state.set_state(AdminBroadcast.waiting_for_text)
    await cb.answer()


@message_router.message(AdminBroadcast.waiting_for_text)
async def broadcast_input_text(msg: types.Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text:
        await msg.answer("РўРµРєСЃС‚ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. Р’РІРµРґРёС‚Рµ РµРіРѕ РµС‰С‘ СЂР°Р·:")
        return

    await state.update_data(text=text)

    kb = InlineKeyboardBuilder()
    kb.button(text="вњ… РџРѕРґС‚РІРµСЂРґРёС‚СЊ С‚РµРєСЃС‚", callback_data="confirm_text")
    kb.button(text="вњЏпёЏ Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ", callback_data="edit_text")
    kb.adjust(2)

    await msg.answer(f"РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ С‚РµРєСЃС‚Р°:\n\n{text}", reply_markup=kb.as_markup())
    await state.set_state(AdminBroadcast.waiting_for_text_confirm)


@message_router.callback_query(AdminBroadcast.waiting_for_text_confirm)
async def broadcast_confirm_text(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()

    if cb.data == "edit_text":
        await cb.message.answer("Р’РІРµРґРёС‚Рµ С‚РµРєСЃС‚ Р·Р°РЅРѕРІРѕ:")
        await state.set_state(AdminBroadcast.waiting_for_text)
        return

    if cb.data != "confirm_text":
        return

    skip_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="РџСЂРѕРїСѓСЃС‚РёС‚СЊ")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await cb.message.answer("РћС‚РїСЂР°РІСЊС‚Рµ С„РѕС‚Рѕ РёР»Рё РЅР°Р¶РјРёС‚Рµ В«РџСЂРѕРїСѓСЃС‚РёС‚СЊВ».", reply_markup=skip_kb)
    await state.set_state(AdminBroadcast.waiting_for_photo)


@message_router.message(AdminBroadcast.waiting_for_photo)
async def broadcast_input_photo(msg: types.Message, state: FSMContext):
    if msg.photo:
        await state.update_data(photo=msg.photo[-1].file_id)
    elif (msg.text or "").strip().lower() == "РїСЂРѕРїСѓСЃС‚РёС‚СЊ":
        await state.update_data(photo=None)
    else:
        await msg.answer("РћС‚РїСЂР°РІСЊС‚Рµ С„РѕС‚Рѕ РёР»Рё РЅР°Р¶РјРёС‚Рµ В«РџСЂРѕРїСѓСЃС‚РёС‚СЊВ».")
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="Р’СЃРµРј Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂР°Рј", callback_data="broadcast_admins")
    kb.button(text="Р’СЃРµРј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј", callback_data="broadcast_all")
    kb.button(text="РџРѕ РєР°С‚РµРіРѕСЂРёРё", callback_data="broadcast_by_category")
    kb.adjust(1)

    await msg.answer(
        "Р’С‹Р±РµСЂРёС‚Рµ СЃРїРѕСЃРѕР± СЂР°СЃСЃС‹Р»РєРё:",
        reply_markup=kb.as_markup()
    )
    await msg.answer("Р РµР¶РёРј РІС‹Р±СЂР°РЅ. РњРѕР¶РЅРѕ СѓР±СЂР°С‚СЊ РєР»Р°РІРёР°С‚СѓСЂСѓ.", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminBroadcast.waiting_for_send_choice)


@message_router.callback_query(AdminBroadcast.waiting_for_send_choice)
async def broadcast_choose_type(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    try:
        if cb.data == "broadcast_by_category":
            with get_db() as db:
                cats = db.query(Category).order_by(Category.name).all()
                cat_items = [(cat.id, cat.name) for cat in cats]

            if not cat_items:
                await cb.message.answer("РљР°С‚РµРіРѕСЂРёР№ РЅРµС‚, РґРѕР±Р°РІСЊС‚Рµ РјРёРЅРёРјСѓРј РѕРґРЅСѓ.")
                return

            kb = InlineKeyboardBuilder()
            for category_id, category_name in cat_items:
                kb.button(text=category_name, callback_data=f"broadcast_cat_{category_id}")
            kb.adjust(2)
            await cb.message.answer("Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ СЂР°СЃСЃС‹Р»РєРё:", reply_markup=kb.as_markup())
            await state.set_state(AdminBroadcast.waiting_for_category)
            return

        if cb.data not in {"broadcast_admins", "broadcast_all"}:
            return

        await do_broadcast(cb, state, mode=cb.data)
    except Exception as exc:
        logger.exception("РћС€РёР±РєР° РЅР° СЌС‚Р°РїРµ РІС‹Р±РѕСЂР° С‚РёРїР° СЂР°СЃСЃС‹Р»РєРё: %s", exc)
        await cb.message.answer("РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР° РїСЂРё РІС‹Р±РѕСЂРµ С‚РёРїР° СЂР°СЃСЃС‹Р»РєРё. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")


@message_router.callback_query(AdminBroadcast.waiting_for_category)
async def broadcast_by_category(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    try:
        cat_id = int(cb.data.split("_")[-1])
    except (TypeError, ValueError):
        await cb.message.answer("РќРµРєРѕСЂСЂРµРєС‚РЅР°СЏ РєР°С‚РµРіРѕСЂРёСЏ.")
        return

    try:
        await do_broadcast(cb, state, mode="broadcast_cat", category_id=cat_id)
    except Exception as exc:
        logger.exception("РћС€РёР±РєР° РїСЂРё СЂР°СЃСЃС‹Р»РєРµ РїРѕ РєР°С‚РµРіРѕСЂРёРё: %s", exc)
        await cb.message.answer("РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР° РїСЂРё Р·Р°РїСѓСЃРєРµ СЂР°СЃСЃС‹Р»РєРё РїРѕ РєР°С‚РµРіРѕСЂРёРё.")


async def do_broadcast(cb: types.CallbackQuery, state: FSMContext, mode: str, category_id: int | None = None):
    data = await state.get_data()
    text = data.get("text", "")
    photo = data.get("photo")
    bot = cb.bot
    sent = 0

    with get_db() as db:
        skip_event_id = (
            db.query(Event.id)
            .filter(Event.event_time >= datetime.utcnow())
            .order_by(Event.event_time.asc())
            .limit(1)
            .scalar()
        )

        if mode == "broadcast_admins":
            user_id_rows = db.query(User.id).filter(User.is_admin.is_(True)).all()
        elif mode == "broadcast_all":
            user_id_rows = db.query(User.id).filter(User.is_registered.is_(True)).all()
        elif mode == "broadcast_cat":
            user_id_rows = (
                db.query(User.id)
                .filter(User.is_registered.is_(True))
                .filter(User.interests.any(Category.id == category_id))
                .all()
            )
        else:
            user_id_rows = []

        user_ids = []
        for (raw_uid,) in user_id_rows:
            try:
                user_ids.append(int(raw_uid))
            except (ValueError, TypeError):
                logger.warning(f"Пропускаем невалидный user_id={raw_uid}")

        if skip_event_id and user_ids:
            registered_rows = (
                db.query(Registration.user_id)
                .filter(Registration.event_id == skip_event_id)
                .filter(Registration.user_id.in_(user_ids))
                .all()
            )
            skip_user_ids = {int(uid) for (uid,) in registered_rows if uid is not None}
            user_ids = [uid for uid in user_ids if uid not in skip_user_ids]

    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, я смогу", callback_data="events_list")],
        [InlineKeyboardButton(text="❌ Нет, не смогу", callback_data="cant_attend")],
    ])

    for uid in user_ids:
        try:
            if photo:
                await bot.send_photo(
                    chat_id=uid,
                    photo=photo,
                    caption=text,
                    parse_mode=None,
                    reply_markup=reply_markup,
                )
            else:
                await bot.send_message(
                    chat_id=uid,
                    text=text,
                    parse_mode=None,
                    reply_markup=reply_markup,
                )
            sent += 1
        except TelegramForbiddenError:
            logger.info("Пользователь %s заблокировал бота", uid)
        except Exception as exc:
            logger.error("Ошибка отправки пользователю %s: %s", uid, exc)

    builder = InlineKeyboardBuilder()
    builder.button(text="Р’ Р°РґРјРёРЅ РїР°РЅРµР»СЊ", callback_data="admin_panel")
    await cb.message.answer(f"Р Р°СЃСЃС‹Р»РєР° Р·Р°РІРµСЂС€РµРЅР°. РћС‚РїСЂР°РІР»РµРЅРѕ: {sent}.", reply_markup=builder.as_markup())
    await state.clear()


@message_router.callback_query(F.data == "cant_attend")
async def handle_cant_attend(cb: types.CallbackQuery):
    await cb.answer()
    await cb.message.answer("Р–Р°Р»СЊ, Р¶РґС‘Рј С‚РµР±СЏ РЅР° СЃР»РµРґСѓСЋС‰РµР№ РёРіСЂРµ.")


class MessageStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message_text = State()


@message_router.callback_query(F.data == "send_priv_message")
async def start_send_message(callback: types.CallbackQuery, state: FSMContext):
    try:
        with get_db() as db:
            users = db.query(User).order_by(User.first_name.asc(), User.last_name.asc()).all()
            user_lines = []
            for user in users:
                full_name = html.escape(f"{user.first_name or ''} {user.last_name or ''}".strip())
                user_lines.append(f"{full_name} вЂ” <code>{user.id}</code>")

        if not user_lines:
            await callback.message.answer("РЎРїРёСЃРѕРє РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РїСѓСЃС‚.")
            return

        chunk_size = 50
        for i in range(0, len(user_lines), chunk_size):
            await callback.message.answer("\n".join(user_lines[i:i + chunk_size]), parse_mode="HTML")

        await callback.message.answer("Р’РІРµРґРёС‚Рµ ID РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ, РєРѕС‚РѕСЂРѕРјСѓ РЅСѓР¶РЅРѕ РѕС‚РїСЂР°РІРёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ:")
        await state.set_state(MessageStates.waiting_for_user_id)
    except Exception as e:
        await callback.message.answer(f"РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё СЃРїРёСЃРєР° РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№: {e}")


@message_router.message(MessageStates.waiting_for_user_id)
async def get_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except (TypeError, ValueError):
        await message.answer("ID РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ С‡РёСЃР»РѕРј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
        return

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()

    if not user:
        await message.answer("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ С‚Р°РєРёРј ID РЅРµ РЅР°Р№РґРµРЅ. Р’РІРµРґРёС‚Рµ ID СЃРЅРѕРІР°.")
        return

    await state.update_data(user_id=user_id)
    await message.answer("Р’РІРµРґРёС‚Рµ С‚РµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ:")
    await state.set_state(MessageStates.waiting_for_message_text)


@message_router.message(MessageStates.waiting_for_message_text)
async def send_message_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="РќР°Р·Р°Рґ", callback_data="admin_panel")
        await message.bot.send_message(chat_id=user_id, text=message.text or "", parse_mode=None, reply_markup=builder.as_markup())
        await message.answer("РЎРѕРѕР±С‰РµРЅРёРµ СѓСЃРїРµС€РЅРѕ РѕС‚РїСЂР°РІР»РµРЅРѕ.")
    except Exception as e:
        await message.answer(f"РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РїСЂР°РІРёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ: {e}")

    await state.clear()
