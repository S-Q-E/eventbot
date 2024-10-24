from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db.database import get_db, User

registration_router = Router()


# Состояния для FSM
class RegistrationStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()


@registration_router.message(Command("start_reg"))
@registration_router.callback_query(F.data == 'start_reg')
async def start_registration(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Начало регистрации, запрос имени
    """
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.delete()
    await state.set_state(RegistrationStates.waiting_for_first_name)
    await callback_query.message.answer("Введите ваше имя: ")


@registration_router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    """
    Обрабатываем имя пользователя и запрашиваем фамилию
    """
    await state.update_data(first_name=message.text)
    await state.set_state(RegistrationStates.waiting_for_last_name)
    await message.answer("Введите вашу фамилию:")


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

    # Обновляем данные пользователя
    if user:
        user.first_name = first_name
        user.last_name = last_name
        user.is_registered = True
        db.commit()
        await message.answer(f"Регистрация завершена, {first_name} {last_name}!\n"
                             f"Теперь вы можете пользоваться <b>полным</b> функционалом бота.")
    else:
        await message.answer("Произошла ошибка при регистрации. Попробуйте снова.")

    await state.clear()