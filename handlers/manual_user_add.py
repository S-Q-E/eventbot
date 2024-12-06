from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from db.database import get_db, User

manual_add_user_router = Router()

class AddManualUser(StatesGroup):
    wait_user_firstname = State()
    wait_user_lastname = State()
    wait_user_phone = State()


@manual_add_user_router.callback_query(F.data == "add_user")
async def add_manual_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите имя нового пользователя: ")
    await state.set_state(AddManualUser.wait_user_firstname)


@manual_add_user_router.message(AddManualUser.wait_user_firstname)
async def get_user_lastname(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите фамилию нового пользователя")
    await state.set_state(AddManualUser.wait_user_lastname)


@manual_add_user_router.message(AddManualUser.wait_user_lastname)
async def get_user_lastname(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Введите номер телефона нового пользователя")
    await state.set_state(AddManualUser.wait_user_phone)


@manual_add_user_router.message(AddManualUser.wait_user_phone)
async def get_user_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    phone = message.text

    id = get_new_id()

    db = next(get_db())

    new_user = User(id, "", first_name, last_name)

    if not phone.isdigit():
        await message.answer("Номер телефона должен быть числом. Проверьте правильность данных")
        return

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    await message.answer(f"✅ Пользователь {first_name} {last_name} добавлен в список зарегистрированных!")
    await state.clear()


