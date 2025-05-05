from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import get_db, Event, Category
from utils.get_coordinates import get_location_by_address

create_event_router = Router()


class Form(StatesGroup):
    name = State()
    address = State()
    event_time = State()
    price = State()
    description = State()
    max_participants = State()
    waiting_for_category = State()


@create_event_router.message(Command("create_event"))
@create_event_router.callback_query(F.data == "create_event")
async def command_start(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_reply_markup()
    await state.set_state(Form.name)
    await callback_query.message.edit_text("📌 <b>Создание нового события</b>\n\n"
                                           "📝 Пожалуйста, введите <b>название события</b>:\n"
                                           "🔹 Пример: <i>Встреча в парке</i>\n\n",
                                           reply_markup=None, parse_mode='HTML')


@create_event_router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.address)
    buttons = [
        InlineKeyboardButton(text="По адресу", callback_data="by_address"),
        InlineKeyboardButton(text="По координатам", callback_data="by_coordinates"),
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await message.reply("📌 <b>Выберите способ добавления места</b>\n\n"
                        "🔹 <i>Вы можете указать место по адресу или координатам</i>",
                        reply_markup=markup)


@create_event_router.callback_query(F.data == "by_address")
async def process_address_choice(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(Form.address)
    await callback_query.message.edit_text("📌 <b>Добавим адрес</b>\n\n"
                                           "📝 Пожалуйста, введите <b>Адрес</b>:\n"
                                           "🔹 Важно! Адрес должен соответствовать такому формату: <i>Москва "
                                           "ул.Сочинская 4</i>\n\n")


@create_event_router.callback_query(F.data == "by_coordinates")
async def process_coordinates_choice(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(Form.address)
    await callback_query.message.edit_text("📌 <b>Добавим координаты</b>\n\n"
                                           "📝 Пожалуйста, введите <b>широту и долготу</b>, разделенные пробелом:\n"
                                           "🔹 Пример: <i>55.7558 37.6173</i>\n\n")


@create_event_router.message(Form.address)
async def process_time(message: types.Message, state: FSMContext):
    address = message.text
    coordinates = get_location_by_address(address)
    if not coordinates:
        await message.reply("Не удалось определить местоположение по введенному адресу\n Попробуйте еще раз")
        return
    await state.update_data(address=message.text)
    await state.set_state(Form.event_time)
    await message.reply("📌 <b>Время</b>\n\n"
                        "📝 Пожалуйста, введите <b>Время события</b>:\n"
                        "🔹 Пример: <i>21/10/2024 20:10</i>\n\n"
                        )


@create_event_router.message(Form.event_time)
async def process_participants(message: types.Message, state: FSMContext):
    try:
        event_time = datetime.strptime(message.text, '%d/%m/%Y %H:%M')
        await state.update_data(event_time=event_time)
        await state.set_state(Form.max_participants)
        await message.reply("📌 <b>Максимальное кол-во участников</b>\n\n"
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
        await message.reply("📌 <b>Цена</b>\n\n"
                            "📝 Пожалуйста, введите <b>цену</b>:\n"
                            "🔹 Пример: <i>10</i>\n\n")
    except ValueError:
        await message.reply("Пожалуйста, введите число")


@create_event_router.message(Form.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(Form.description)
    await message.reply("📌 <b>Введите описание события</b>\n\n"
                        "📝 Пожалуйста, введите <b>описание события или свои комментарии</b>:\n"
                        )


@create_event_router.message(Form.description)
async def process_max_part(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    db = next(get_db())
    categories = db.query(Category).order_by(Category.name).all()
    db.close()

    if not categories:
        await message.answer("Категории не найдены. Пожалуйста, добавьте категории перед созданием события.")
        return
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"event_cat_{category.id}"
        )
    builder.adjust(2)
    await message.answer(
        "Выберите категорию события:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(Form.waiting_for_category)


@create_event_router.callback_query(Form.waiting_for_category)
async def adding_to_db(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[-1])
    await state.update_data(category_id=cat_id)
    event_data = await state.get_data()
    db = next(get_db())
    new_event = Event(
        name=event_data['name'],
        description=event_data['description'],
        address=event_data['address'],
        event_time=event_data['event_time'],
        max_participants=int(event_data['max_participants']),
        price=int(event_data['price']),
        category_id=int(event_data['category_id'])
    )
    db.add(new_event)
    db.commit()
    all_events_btn = InlineKeyboardButton(text="Просмотреть все события", callback_data="events_page_1")
    markup = InlineKeyboardMarkup(inline_keyboard=[[all_events_btn]])
    await callback.message.reply(f"☑️☑️☑️Готово! Событие <b>{new_event.name}</b> успешно создано!", reply_markup=markup)
    await state.clear()
    db.close()
