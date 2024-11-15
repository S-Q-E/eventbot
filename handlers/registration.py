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
    waiting_for_last_name = State()
    waiting_for_phone_number = State()


@registration_router.callback_query(F.data == 'start_reg')
async def start_registration(callback: types.CallbackQuery, state: FSMContext):
    """
    Начало регистрации, запрос имени
    """
    user_id = callback.from_user.id
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        if user.is_registered:
            events_button = InlineKeyboardButton(text="События", callback_data="events")
            my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")
            markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button]])
            await callback.message.answer(f"❗<b>{user.first_name}, вам не нужна регистрация</b>", reply_markup=markup)
        else:
            await state.set_state(RegistrationStates.waiting_for_first_name)
            await callback.message.answer("Введите ваше имя: ")


@registration_router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    """
    Обрабатываем имя пользователя и запрашиваем фамилию
    """
    await state.update_data(first_name=message.text)
    await state.set_state(RegistrationStates.waiting_for_last_name)
    await message.answer("Введите вашу фамилию: ")


@registration_router.message(RegistrationStates.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    """
    Обрабатываем фамилию пользователя и запрашиваем номер телефона
    """
    await state.update_data(last_name=message.text)
    await state.set_state(RegistrationStates.waiting_for_phone_number)

    # Кнопка для отправки номера телефона
    request_phone_button = KeyboardButton(text="Отправить номер телефона", request_contact=True)
    phone_keyboard = ReplyKeyboardMarkup(keyboard=[[request_phone_button]], resize_keyboard=True,
                                         one_time_keyboard=True)

    await message.answer("Пожалуйста, отправьте ваш номер телефона:", reply_markup=phone_keyboard)


@registration_router.message(RegistrationStates.waiting_for_phone_number)
@registration_router.message(RegistrationStates.waiting_for_phone_number, F.contact)
async def process_phone_number(message: types.Message, state: FSMContext):
    """
    Обрабатываем номер телефона и завершаем регистрацию
    """
    user_data = await state.get_data()
    first_name = user_data['first_name']
    last_name = user_data['last_name']
    phone_number = message.contact.phone_number

    user_id = message.from_user.id
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()

    try:
        if user:
            user.first_name = first_name
            user.last_name = last_name
            user.is_registered = True
            user.phone_number = phone_number
            db.commit()
            await message.answer(f"<b>Регистрация завершена, {first_name} {last_name}!\n"
                                 f"Все функции доступны!</b>")
        else:
            await message.answer("Что-то пошло не так...")
            await state.clear()
    except Exception as ex:
        logger.error(f"Ошибка при регистрации: {ex}")
    finally:
        await message.answer("Нажмите кнопку 'start'")
        await state.clear()
