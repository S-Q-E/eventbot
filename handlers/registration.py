import logging
import re
import html
from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot import logger
from db.database import get_db, User

registration_router = Router()


# Состояния для FSM
class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_phone_number = State()

import html

@registration_router.callback_query(F.data == 'start_reg')
async def start_registration(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            if user.is_registered:
                # ...

                events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
                user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")
                markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_help]])
                safe_name = html.escape(user.first_name or "")
                await callback.message.answer(f"❗<b>{safe_name}, вам не нужна регистрация</b>", reply_markup=markup)
            else:
                await state.set_state(RegistrationStates.waiting_for_first_name)
                await callback.message.answer("Введите ваше имя и фамилию через пробел: ")


@registration_router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    """
    Обрабатываем имя пользователя и запрашиваем фамилию
    """
    try:
        name_parts = message.text.strip().split()
        if len(name_parts) != 2:
            await message.answer("❗ Пожалуйста, введите имя и фамилию через пробел. Пример: Иван Иванов")
            return

        first_name, last_name = name_parts
        if not all(re.match(r"^[А-Яа-яA-Za-z-]+$", name) for name in [first_name, last_name]):
            await message.answer(
                "❗ Имя и фамилия должны содержать только буквы (допустимы дефисы). Попробуйте снова."
            )
            return

        request_phone_button = KeyboardButton(text="Отправить номер телефона", request_contact=True)
        phone_keyboard = ReplyKeyboardMarkup(keyboard=[[request_phone_button]], resize_keyboard=True,
                                             one_time_keyboard=True)
        await message.answer("Пожалуйста, отправьте ваш номер телефона:", reply_markup=phone_keyboard)
        await state.set_state(RegistrationStates.waiting_for_phone_number)
        await state.update_data(first_name=first_name,
                                last_name=last_name)
    except ValueError as e:
        logging.info(f"Пользователь ввел недостаточно данных ошибка {e}")
        await message.answer("Вы ввели неполные данные,")


@registration_router.message(RegistrationStates.waiting_for_phone_number)
@registration_router.message(RegistrationStates.waiting_for_phone_number, F.contact)
async def process_phone_number(message: types.Message, state: FSMContext):
    """
    Обрабатываем номер телефона и завершаем регистрацию
    """

    if message.contact:
        phone_number = message.contact.phone_number
    else:
        # Проверка формата введенного номера
        phone_number = message.text.strip()
        if not re.match(r'^\+7\d', phone_number):
            await message.answer("❗ Номер телефона должен начинаться с +7 и содержать 11 цифр. Попробуйте снова:")
            return

    user_data = await state.get_data()
    first_name = user_data['first_name']
    last_name = user_data['last_name']

    user_id = message.from_user.id
    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()

        try:
            if user:
                user.first_name = first_name
                user.last_name = last_name
                user.is_registered = True
                user.phone_number = phone_number
                # db.commit() is handled by context manager
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]])
                safe_first_name = html.escape(first_name)
                safe_last_name = html.escape(last_name)
                await message.answer(f"<b>Регистрация завершена, {safe_first_name} {safe_last_name}!\n"
                                     f"Все функции доступны!</b>", reply_markup=markup)
            else:
                await message.answer("Что-то пошло не так...")
                await state.clear()
        except Exception as ex:
            logger.error(f"Ошибка при регистрации: {ex}")
        finally:
            await state.clear()
