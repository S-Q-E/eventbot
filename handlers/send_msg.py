import logging
from aiogram import Router, Bot, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.database import get_db, User, Registration, Category
from utils.get_nearest_events import get_nearest_event

logger = logging.getLogger(__name__)
message_router = Router()


class AdminBroadcast(StatesGroup):
    waiting_for_text = State()
    waiting_for_text_confirm = State()   # ← Новое состояние! подтверждение текста
    waiting_for_photo = State()
    waiting_for_send_choice = State()
    waiting_for_category = State()


# 1) Старт диалога рассылки
@message_router.callback_query(F.data == "send_to_users")
async def cmd_broadcast_start(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.edit_reply_markup()
    await cb.message.answer("Введите текст рассылки:")
    await state.set_state(AdminBroadcast.waiting_for_text)
    await cb.answer()


# 2) Ввод текста
@message_router.message(AdminBroadcast.waiting_for_text)
async def broadcast_input_text(msg: types.Message, state: FSMContext):
    text = msg.text.strip()
    if not text:
        return await msg.answer("Текст не может быть пустым, введите ещё раз:")
    await state.update_data(text=text)

    # Превью и кнопка подтверждения текста
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить текст", callback_data="confirm_text")
    kb.button(text="❌ Редактировать",    callback_data="edit_text")
    kb.adjust(2)
    await msg.answer(f"Предпросмотр текста:\n\n{text}", reply_markup=kb.as_markup())
    await state.set_state(AdminBroadcast.waiting_for_text_confirm)


# 3) Подтверждение текста
@message_router.callback_query(AdminBroadcast.waiting_for_text_confirm)
async def broadcast_confirm_text(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.data == "edit_text":
        await cb.message.answer("Введите текст заново:")
        return await state.set_state(AdminBroadcast.waiting_for_text)

    # Идём дальше — просим фото
    await cb.message.answer("Отправьте фото или «пропустить» для рассылки без фото.")
    await state.set_state(AdminBroadcast.waiting_for_photo)


# 4) Ввод фото (или пропуск)
@message_router.message(AdminBroadcast.waiting_for_photo)
async def broadcast_input_photo(msg: types.Message, state: FSMContext):
    if msg.photo:
        photo_id = msg.photo[-1].file_id
        await state.update_data(photo=photo_id)
    elif msg.text.lower() == "пропустить":
        await state.update_data(photo=None)
    else:
        return await msg.answer("Отправьте фото или «пропустить».")

    # Выбор типа рассылки
    kb = InlineKeyboardBuilder()
    kb.button(text="Всем администраторам", callback_data="broadcast_admins")
    kb.button(text="Всем пользователям", callback_data="broadcast_all")
    kb.button(text="По категории", callback_data="broadcast_by_category")
    kb.adjust(1)
    await msg.answer("Выберите способ рассылки:", reply_markup=kb.as_markup())
    await state.set_state(AdminBroadcast.waiting_for_send_choice)


# 5) Выбор способа рассылки
@message_router.callback_query(AdminBroadcast.waiting_for_send_choice)
async def broadcast_choose_type(cb: types.CallbackQuery, state: FSMContext):
    choice = cb.data
    await cb.answer()

    if choice == "broadcast_by_category":
        # Предлагаем выбрать категорию
        db = next(get_db())
        cats = db.query(Category).order_by(Category.name).all()
        db.close()
        if not cats:
            return await cb.message.answer("Категорий нет, добавьте минимум одну.")
        kb = InlineKeyboardBuilder()
        for c in cats:
            kb.button(text=c.name, callback_data=f"broadcast_cat_{c.id}")
        kb.adjust(2)
        await cb.message.answer("Выберите категорию для рассылки:", reply_markup=kb.as_markup())
        return await state.set_state(AdminBroadcast.waiting_for_category)

    # Иначе сразу рассылаем
    await do_broadcast(cb, state, mode=choice)


# 6) Рассылка по конкретной категории
@message_router.callback_query(AdminBroadcast.waiting_for_category)
async def broadcast_by_category(cb: types.CallbackQuery, state: FSMContext):
    cat_id = int(cb.data.split("_")[-1])
    await cb.answer()
    await do_broadcast(cb, state, mode="broadcast_cat", category_id=cat_id)


# Общая функция рассылки
async def do_broadcast(cb: types.CallbackQuery, state: FSMContext, mode: str, category_id: int = None):
    data = await state.get_data()
    text = data["text"]
    photo = data.get("photo")
    bot = cb.bot
    sent = 0

    # Определяем ближайшее событие для фильтра «уже записались»
    event = await get_nearest_event()
    skip_event = event.id if event else None

    db = next(get_db())
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

    for usr in users:
        try:
            uid = int(usr.id)
        except (ValueError, TypeError):
            logger.warning(f"Пропускаем невалидный user_id={usr.id}")
            continue

        if skip_event:
            if db.query(Registration).filter_by(user_id=uid, event_id=skip_event).first():
                continue

        reply_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, я смогу", callback_data="events_list")],
            [InlineKeyboardButton(text="❌ Нет, не смогу", callback_data="cant_attend")]
        ])

        try:
            if photo:
                await bot.send_photo(chat_id=uid, photo=photo, caption=text, reply_markup=reply_markup)
            else:
                await bot.send_message(chat_id=uid, text=text, reply_markup=reply_markup)
            sent += 1
        except TelegramForbiddenError:
            logger.info(f"Пользователь {uid} заблокировал бота")
        except Exception as e:
            logger.error(f"Ошибка при отправке {uid}: {e}")

    db.close()
    builder = InlineKeyboardBuilder()
    builder.button(text="В админ панель", callback_data="admin_panel")
    await cb.message.answer(f"Рассылка завершена. Отправлено: {sent}.", reply_markup=builder.as_markup())
    await state.clear()


@message_router.callback_query(F.data == "cant_attend")
async def handle_cant_attend(cb: types.CallbackQuery):
    await cb.answer()
    await cb.message.answer("Жаль, ждем тебя на следующей игре.")


class MessageStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message_text = State()


@message_router.callback_query(F.data == "send_priv_message")
async def start_send_message(callback: types.CallbackQuery, state: FSMContext):
    try:
        db = next(get_db())
        users = db.query(User).order_by(User.first_name.asc(), User.last_name.asc()).all()
        if not users:
            await callback.message.answer("Список пользователей пуст.")
            return

        user_lines = []
        for user in users:
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            user_line = f"{full_name} — <code>{user.id}</code>"
            user_lines.append(user_line)

        # Разделим список на части по 50 пользователей
        chunk_size = 50
        for i in range(0, len(user_lines), chunk_size):
            chunk = user_lines[i:i + chunk_size]
            text = "\n".join(chunk)
            await callback.message.answer(text)

        await callback.message.answer("Введите ID пользователя, которому нужно отправить сообщение:")
        await state.set_state(MessageStates.waiting_for_user_id)
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении списка пользователей: {e}")


@message_router.message(MessageStates.waiting_for_user_id)
async def get_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await message.answer("Пользователь с таким ID не найден. Введите ID снова.")
            return

        await state.update_data(user_id=user_id)
        await message.answer("Введите текст сообщения:")
        await state.set_state(MessageStates.waiting_for_message_text)
    except ValueError:
        await message.answer("ID должен быть числом. Попробуйте снова.")
    except Exception as e:
        await message.answer(f"Ошибка при обработке ID: {e}")


@message_router.message(MessageStates.waiting_for_message_text)
async def send_message_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="Назад", callback_data="admin_panel")
        await message.bot.send_message(chat_id=user_id, text=message.text, reply_markup=builder.as_markup())
        await message.answer("Сообщение успешно отправлено.")
    except Exception as e:
        await message.answer(f"Не удалось отправить сообщение: {e}")
    await state.clear()
