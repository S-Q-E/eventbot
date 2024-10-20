from datetime import datetime

from aiogram import Router, types,F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from db.database import get_db, Event


create_event_router = Router()


class Form(StatesGroup):
    name = State()
    address = State()
    event_time = State()
    description = State()


@create_event_router.callback_query(F.data == "create_event")
async def command_start(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Form.name)
    await message.answer("Введите название события: ", reply_markup=ReplyKeyboardRemove())


@create_event_router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)  # Сохранение имени
    await state.set_state(Form.address)  # Переход к следующему состоянию
    await message.reply("Добавьте адрес: ")


@create_event_router.message(Form.address)
async def process_time(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(Form.event_time)
    await message.answer("Введите время создаваемого события")


@create_event_router.message(Form.event_time)
async def process_desc(message: types.Message, state: FSMContext):
    try:
        event_time = datetime.strptime(message.text, '%d/%m/%Y %H:%M')
        await state.update_data(event_time=event_time)
        await state.set_state(Form.description)
        await message.reply("Введите описание события: ")
    except ValueError:
        await message.reply("Неверный формат даты. Попробуйте снова в формате ДД/ММ/ГГГГ ЧЧ:ММ.")


@create_event_router.message(Form.description)
async def adding_to_db(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    event_data = await state.get_data()
    db = next(get_db())  # Используем асинхронную сессию
    new_event = Event(
        name=event_data['name'],
        description=event_data['description'],
        address=event_data['address'],
        event_time=event_data['event_time']
    )
    db.add(new_event)
    db.commit()  # Асинхронно фиксируем изменения
    db.refresh(new_event)  # Обновляем объект события из базы данных

    await message.reply(f"Событие '{new_event.name}' успешно создано и сохранено в базе данных!")
    await state.clear()
