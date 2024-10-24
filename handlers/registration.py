from aiogram.fsm.state import State, StatesGroup
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.database import get_db, User

registration_router = Router()


class UserReg(StatesGroup):
    first_name = State()
    last_name = State()


@registration_router.callback_query(F.data == "start_reg")
@registration_router.message(Command("start_reg"))
async def start_registration(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    # await callback_query.message.delete(chat_id=)
    await callback_query.message.answer("Пожалуйста, введите имя")
    # await message.answer("Пожалуйста, введите ваше имя:")
    await state.set_state(UserReg.first_name)


# Шаг 2: Получение имени и запрос фамилии
@registration_router.message(UserReg.first_name)
async def get_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Теперь введите вашу фамилию:")
    await state.set_state(UserReg.last_name)


# Шаг 3: Получение фамилии и завершение регистрации
@registration_router.message(UserReg.last_name)
async def get_last_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    first_name = data['first_name']
    last_name = message.text

    # Сохранение пользователя в базу данных
    db = next(get_db())
    user = db.query(User).filter_by(username=message.from_user.username).first()
    if user:
        user.first_name = first_name
        user.last_name = last_name
    else:
        user = User(username=message.from_user.username, first_name=first_name, last_name=last_name, is_registrated=True)
        db.add(user)

    db.commit()

    await message.answer(f"Регистрация завершена, {first_name} {last_name}!")
    await state.clear()
