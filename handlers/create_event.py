from aiogram import Router, types,F
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove

create_event_router = Router()


class Form(StatesGroup):
    name = State()
    adress = State()
    event_time = State()
    desctiption = State()


@create_event_router.callback_query(F.data == "create_event")
async def command_start(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("Введите название события: ", reply_markup=ReplyKeyboardRemove())


@create_event_router.message(F.state==Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)  # Сохранение имени
    await state.set_state(Form.adress)  # Переход к следующему состоянию
    await message.reply("Добавьте адрес: ")


@create_event_router.message(F.state==Form.adress)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(adress=message.text)
    await state.set_state(Form.event_time)
    await message.answer("Когда и во сколько? Введи в формате дд/мм \n")
    # user_data = await state.get_data()  # Получение всех данных
    # await message.reply(f"Привет, {user_data['name']}! Тебе {user_data['age']} лет.")


@create_event_router.message(F.state==Form.event_time)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(event_time=message.text)
    await state.set_state(Form.desctiption)
    await message.answer("Введите описание события или оставьте комментарий к событию ")


@create_event_router.message(F.state==Form.desctiption)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    event_data = await state.get_data()
    await message.answer(f"Событие {event_data['name']}\n"
                         f"Время: {event_data['event_time']}\n"
                         f"Место: {event_data['adress']}\n"
                         f"Место: {event_data['description']}")
    await state.clear()

