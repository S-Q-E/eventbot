from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from db.database import get_db, Event
from utils.get_coordinates import get_location_by_address

import locale

locale.setlocale(
    category=locale.LC_ALL,
    locale="Russian"
)

create_event_router = Router()


class Form(StatesGroup):
    name = State()
    address = State()
    event_time = State()
    price = State()
    description = State()
    max_participants = State()


@create_event_router.message(Command("create_event"))
@create_event_router.callback_query(F.data == "create_event")
async def command_start(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_reply_markup()
    await state.set_state(Form.name)
    await callback_query.message.edit_text("📌 <b>Шаг 1 из 6: Создание нового события</b>\n\n"
                                           "📝 Пожалуйста, введите <b>название события</b>:\n"
                                           "🔹 Пример: <i>Встреча в парке</i>\n\n",
                                           reply_markup=None, parse_mode='HTML')


@create_event_router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)  # Сохранение имени
    await state.set_state(Form.address)  # Переход к следующему состоянию
    await message.reply("📌 <b>Шаг 2 из 6: Добавим адрес</b>\n\n"
                        "📝 Пожалуйста, введите <b>Адрес</b>:\n"
                        "🔹 Важно! Адрес должен соответствовать такому формату: <i>Москва ул.Сочинская 4</i>\n\n"
                        )


@create_event_router.message(Form.address)
async def process_time(message: types.Message, state: FSMContext):
    address = message.text
    coordinates = get_location_by_address(address)
    if not coordinates:
        await message.reply("Не удалось определить местоположение по введенному адресу\n Попробуйте еще раз")
        return
    await state.update_data(address=message.text)
    await state.set_state(Form.event_time)
    await message.reply("📌 <b>Шаг 3 из 6: Введите время события</b>\n\n"
                        "📝 Пожалуйста, введите <b>Время события</b>:\n"
                        "🔹 Пример: <i>21/10/2024 20:10</i>\n\n"
                        )


@create_event_router.message(Form.event_time)
async def process_participants(message: types.Message, state: FSMContext):
    try:
        event_time = datetime.strptime(message.text, '%d/%m/%Y %H:%M')
        await state.update_data(event_time=event_time)
        await state.set_state(Form.max_participants)
        await message.reply("📌 <b>Шаг 4 из 6: Максимальное кол-во участников</b>\n\n"
                            "📝 Пожалуйста, введите <b>максимальное количество участников</b>:\n"
                            "🔹 Пример: <i>10</i>\n\n")
    except ValueError:
        await message.reply("Неверный формат даты. Попробуйте снова в формате ДД/ММ/ГГГГ ЧЧ:ММ.")


@create_event_router.message(Form.max_participants)
async def process_desc(message: types.Message, state: FSMContext):
    try:
        max_participants = message.text
        await state.update_data(max_participants=max_participants)
        await state.set_state(Form.price)
        await message.reply("📌 <b>Шаг 5 из 6: Цена</b>\n\n"
                            "📝 Пожалуйста, введите <b>цену</b>:\n"
                            "🔹 Пример: <i>10</i>\n\n")
    except ValueError:
        await message.reply("Пожалуйста, введите число")


@create_event_router.message(Form.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(Form.description)
    await message.reply("📌 <b>Последний шаг: Описание</b>\n\n"
                        "📝 Пожалуйста, введите <b>описание события или свои комментарии</b>:\n"
                        )


@create_event_router.message(Form.description)
async def adding_to_db(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    event_data = await state.get_data()
    db = next(get_db())
    new_event = Event(
        name=event_data['name'],
        description=event_data['description'],
        address=event_data['address'],
        event_time=event_data['event_time'],
        max_participants=int(event_data['max_participants']),
        price=int(event_data['price'])
    )
    db.add(new_event)
    db.commit()
    all_events_btn = InlineKeyboardButton(text="Просмотреть все события", callback_data="events_page_1")
    markup = InlineKeyboardMarkup(inline_keyboard=[[all_events_btn]])
    await message.reply(f"☑️☑️☑️Готово! Событие <b>{new_event.name}</b> успешно создано!", reply_markup=markup)
    await state.clear()
    db.close()
