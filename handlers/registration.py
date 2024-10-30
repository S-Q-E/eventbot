import logging

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot import logger
from db.database import get_db, User

registration_router = Router()


# Состояния для FSM
class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()


@registration_router.message(Command("start_reg"))
@registration_router.callback_query(F.data == 'start_reg')
async def start_registration(message: types.Message, state: FSMContext):
    """
    Начало регистрации, запрос имени
    """
    user_id = message.from_user.id
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()

    if user.is_registered:
        create_event = InlineKeyboardButton(text="Создать событие", callback_data="create_event")
        events_button = InlineKeyboardButton(text="События", callback_data="events")
        my_events_button = InlineKeyboardButton(text="Мои записи", callback_data="my_events")

        markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button], [create_event]])
        await message.answer(f"❗<b>{user.first_name} вам не нужна регистрация</b>", reply_markup=markup, parse_mode='HTML')
    else:
        await state.set_state(RegistrationStates.waiting_for_first_name)
        await message.answer("Введите ваше имя: ")


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
    Обрабатываем фамилию пользователя и завершаем регистрацию
    """
    user_data = await state.get_data()
    first_name = user_data['first_name']
    last_name = message.text

    user_id = message.from_user.id
    db = next(get_db())
    user = db.query(User).filter_by(id=user_id).first()

    try:                # Обновляем данные пользователя
        if user:
            user.first_name = first_name
            user.last_name = last_name
            user.is_registered = True
            db.commit()
            await message.answer(f"<b>Регистрация завершена, {first_name} {last_name}!\n"
                                 f"Все функции доступны!</b> ")
        else:
            await message.answer("Что то пошло не так...")
            await state.clear()
    except Exception as ex:
        logger.info(f"Ошибка при регистрации. Что то не то в базой данных.{ex}")
    finally:
            await message.answer("Нажмите кнопку 'start' ")