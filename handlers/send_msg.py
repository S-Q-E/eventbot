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
    await cb.message.answer("Введите текст рассылки:")
    await state.set_state(AdminBroadcast.waiting_for_text)
    await cb.answer()


@message_router.message(AdminBroadcast.waiting_for_text)
async def broadcast_input_text(msg: types.Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text:
        await msg.answer("Текст не может быть пустым. Введите его ещё раз:")
        return

    await state.update_data(text=text)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить текст", callback_data="confirm_text")
    kb.button(text="✏️ Редактировать", callback_data="edit_text")
    kb.adjust(2)

    await msg.answer(f"Предпросмотр текста:\n\n{text}", reply_markup=kb.as_markup())
    await state.set_state(AdminBroadcast.waiting_for_text_confirm)


@message_router.callback_query(AdminBroadcast.waiting_for_text_confirm)
async def broadcast_confirm_text(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()

    if cb.data == "edit_text":
        await cb.message.answer("Введите текст заново:")
        await state.set_state(AdminBroadcast.waiting_for_text)
        return

    if cb.data != "confirm_text":
        return

    skip_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await cb.message.answer("Отправьте фото или нажмите «Пропустить».", reply_markup=skip_kb)
    await state.set_state(AdminBroadcast.waiting_for_photo)


@message_router.message(AdminBroadcast.waiting_for_photo)
async def broadcast_input_photo(msg: types.Message, state: FSMContext):
    if msg.photo:
        await state.update_data(photo=msg.photo[-1].file_id)
    elif (msg.text or "").strip().lower() == "пропустить":
        await state.update_data(photo=None)
    else:
        await msg.answer("Отправьте фото или нажмите «Пропустить».")
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="Всем администраторам", callback_data="broadcast_admins")
    kb.button(text="Всем пользователям", callback_data="broadcast_all")
    kb.button(text="По категории", callback_data="broadcast_by_category")
    kb.adjust(1)

    await msg.answer(
        "Выберите способ рассылки:",
        reply_markup=kb.as_markup()
    )
    await msg.answer("Режим выбран. Можно убрать клавиатуру.", reply_markup=ReplyKeyboardRemove())
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
                await cb.message.answer("Категорий нет, добавьте минимум одну.")
                return

            kb = InlineKeyboardBuilder()
            for category_id, category_name in cat_items:
                kb.button(text=category_name, callback_data=f"broadcast_cat_{category_id}")
            kb.adjust(2)
            await cb.message.answer("Выберите категорию для рассылки:", reply_markup=kb.as_markup())
            await state.set_state(AdminBroadcast.waiting_for_category)
            return

        if cb.data not in {"broadcast_admins", "broadcast_all"}:
            return

        await do_broadcast(cb, state, mode=cb.data)
    except Exception as exc:
        logger.exception("Ошибка на этапе выбора типа рассылки: %s", exc)
        await cb.message.answer("Произошла ошибка при выборе типа рассылки. Попробуйте снова.")


@message_router.callback_query(AdminBroadcast.waiting_for_category)
async def broadcast_by_category(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    try:
        cat_id = int(cb.data.split("_")[-1])
    except (TypeError, ValueError):
        await cb.message.answer("Некорректная категория.")
        return

    try:
        await do_broadcast(cb, state, mode="broadcast_cat", category_id=cat_id)
    except Exception as exc:
        logger.exception("Ошибка при рассылке по категории: %s", exc)
        await cb.message.answer("Произошла ошибка при запуске рассылки по категории.")


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
            users = db.query(User).filter(User.is_admin == True).all()
        elif mode == "broadcast_all":
            users = db.query(User).filter(User.is_registered == True).all()
        elif mode == "broadcast_cat":
            users = (
                db.query(User)
                .filter(User.is_registered == True)
                .filter(User.interests.any(Category.id == category_id))
                .all()
            )
        else:
            users = []

        for user in users:
            uid = int(user.id)

            if skip_event_id and db.query(Registration).filter_by(user_id=uid, event_id=skip_event_id).first():
                continue

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да, я смогу", callback_data="events_list")],
                [InlineKeyboardButton(text="❌ Нет, не смогу", callback_data="cant_attend")],
            ])

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
    builder.button(text="В админ панель", callback_data="admin_panel")
    await cb.message.answer(f"Рассылка завершена. Отправлено: {sent}.", reply_markup=builder.as_markup())
    await state.clear()


@message_router.callback_query(F.data == "cant_attend")
async def handle_cant_attend(cb: types.CallbackQuery):
    await cb.answer()
    await cb.message.answer("Жаль, ждём тебя на следующей игре.")


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
                user_lines.append(f"{full_name} — <code>{user.id}</code>")

        if not user_lines:
            await callback.message.answer("Список пользователей пуст.")
            return

        chunk_size = 50
        for i in range(0, len(user_lines), chunk_size):
            await callback.message.answer("\n".join(user_lines[i:i + chunk_size]), parse_mode="HTML")

        await callback.message.answer("Введите ID пользователя, которому нужно отправить сообщение:")
        await state.set_state(MessageStates.waiting_for_user_id)
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении списка пользователей: {e}")


@message_router.message(MessageStates.waiting_for_user_id)
async def get_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except (TypeError, ValueError):
        await message.answer("ID должен быть числом. Попробуйте снова.")
        return

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()

    if not user:
        await message.answer("Пользователь с таким ID не найден. Введите ID снова.")
        return

    await state.update_data(user_id=user_id)
    await message.answer("Введите текст сообщения:")
    await state.set_state(MessageStates.waiting_for_message_text)


@message_router.message(MessageStates.waiting_for_message_text)
async def send_message_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="Назад", callback_data="admin_panel")
        await message.bot.send_message(chat_id=user_id, text=message.text or "", parse_mode=None, reply_markup=builder.as_markup())
        await message.answer("Сообщение успешно отправлено.")
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение: {e}")

    await state.clear()
