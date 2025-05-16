from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from db.database import get_db, User
from utils.id_generator import generate_unique_id_with_uuid

manual_add_user_router = Router()


class AddManualUser(StatesGroup):
    wait_user_firstname = State()
    wait_user_phone = State()


@manual_add_user_router.callback_query(F.data == "add_user")
async def add_manual_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите имя и фамилию нового пользователя <b>через пробел</b>: ")
    await state.set_state(AddManualUser.wait_user_firstname)


@manual_add_user_router.message(AddManualUser.wait_user_firstname)
async def get_user_lastname(message: types.Message, state: FSMContext):
    try:
        first_name, last_name = message.text.split(" ")
        await state.update_data(first_name=first_name)
        await state.update_data(last_name=last_name)
        await message.answer("Теперь введите номер телефона")
        await state.set_state(AddManualUser.wait_user_phone)
    except IndexError as e:
        await message.answer("Проверьте правильность введения данных. Нужно вводить через пробел")
        return


@manual_add_user_router.message(AddManualUser.wait_user_phone)
async def get_user_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    phone = message.text
    with next(get_db()) as db:

        new_id = generate_unique_id_with_uuid(db)
        if not phone.startswith("+7"):
            await message.answer("Номер телефона должен начинаться с +7. Проверьте правильность данных")
            return

        new_user = User(
            id=new_id,
            username=None,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            is_admin=False,
            is_registered=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()

    back_btn = InlineKeyboardButton(text="Назад", callback_data="admin_panel")
    markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
    await message.answer(f"✅ Пользователь {first_name} {last_name} добавлен в список зарегистрированных!\n"
                         f"Перейдите в редактирование события, чтобы добавить участника к событию", reply_markup=markup)
    await state.clear()


