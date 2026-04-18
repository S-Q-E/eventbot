import logging
import re
import html

from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db.database import get_db, User

registration_router = Router()
logger = logging.getLogger(__name__)


class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_phone_number = State()


@registration_router.callback_query(F.data == "start_reg")
async def start_registration(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id, username=callback.from_user.username)
            db.add(user)

        if user.is_registered:
            events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
            user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")
            markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_help]])
            safe_name = html.escape(user.first_name or callback.from_user.first_name or "Пользователь")
            await callback.message.answer(f"<b>{safe_name}, вам не нужна повторная регистрация.</b>", reply_markup=markup)
            await callback.answer()
            return

    await state.set_state(RegistrationStates.waiting_for_first_name)
    await callback.message.answer("Введите ваше имя и фамилию через пробел. Пример: Иван Иванов")
    await callback.answer()


@registration_router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    name_parts = (message.text or "").strip().split()
    if len(name_parts) < 2:
        await message.answer("Пожалуйста, введите имя и фамилию через пробел. Пример: Иван Иванов")
        return

    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:])

    if not all(re.match(r"^[А-Яа-яA-Za-z-]+$", name) for name in [first_name, last_name.replace(" ", "")]):
        await message.answer("Имя и фамилия должны содержать только буквы (дефис допустим).")
        return

    request_phone_button = KeyboardButton(text="Отправить номер телефона", request_contact=True)
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[request_phone_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.update_data(first_name=first_name, last_name=last_name)
    await state.set_state(RegistrationStates.waiting_for_phone_number)
    await message.answer("Пожалуйста, отправьте ваш номер телефона (кнопкой или текстом в формате +7XXXXXXXXXX).", reply_markup=phone_keyboard)


@registration_router.message(RegistrationStates.waiting_for_phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    if message.contact:
        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer("Отправьте, пожалуйста, свой собственный контакт.")
            return
        phone_number = message.contact.phone_number
    else:
        phone_number = (message.text or "").strip()

    if not re.match(r"^\+7\d{10}$", phone_number):
        await message.answer("Номер телефона должен быть в формате +7XXXXXXXXXX. Попробуйте снова.")
        return

    user_data = await state.get_data()
    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    user_id = message.from_user.id

    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id, username=message.from_user.username)
            db.add(user)

        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        user.is_registered = True

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]]
    )
    safe_first_name = html.escape(first_name)
    safe_last_name = html.escape(last_name)
    await message.answer(
        f"<b>Регистрация завершена, {safe_first_name} {safe_last_name}!\nВсе функции доступны.</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await message.answer("Контакт сохранён.", reply_markup=ReplyKeyboardRemove())
    await state.clear()
