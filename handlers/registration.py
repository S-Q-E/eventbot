from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from db.database import get_db, User

registration_router = Router()


# Шаг 1: Запрос имени
@registration_router.message(commands=["start_reg"])
@registration_router.callback_query(F.data == "start_reg")
async def start_registration(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, введите ваше имя:")
    await state.set_state("get_first_name")


# Шаг 2: Получение имени и запрос фамилии
@registration_router.message(state="get_first_name")
async def get_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Теперь введите вашу фамилию:")
    await state.set_state("get_last_name")


# Шаг 3: Получение фамилии и завершение регистрации
@registration_router.message(state="get_last_name")
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
        user = User(username=message.from_user.username, first_name=first_name, last_name=last_name)
        db.add(user)

    db.commit()

    await message.answer(f"Регистрация завершена, {first_name} {last_name}!")
    await state.clear()
