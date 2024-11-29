import logging

from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db.database import get_db, Event
from utils.get_coordinates import get_location_by_address

edit_event_router = Router()

back_btn = InlineKeyboardButton(text="Назад",
                                     callback_data="delete_event_button")
markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])


class EditEventStates(StatesGroup):
    editing_name = State()
    editing_time = State()
    editing_desc = State()
    editing_participants = State()
    editing_price = State()
    editing_address = State()


@edit_event_router.callback_query(F.data.startswith("edit_event_"))
async def edit_event(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[-1])
    # Меню для выбора параметра редактирования
    edit_options_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"edit_name_{event_id}")],
            [InlineKeyboardButton(text="📍 Адрес", callback_data=f"edit_address_{event_id}")],
            [InlineKeyboardButton(text="🕒 Время", callback_data=f"edit_time_{event_id}")],
            [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price_{event_id}")],
            [InlineKeyboardButton(text="🗓 Описание", callback_data=f"edit_desc_{event_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="delete_event_button")]
        ]
    )
    await callback_query.message.answer(
        "Выберите, что хотите редактировать:",
        reply_markup=edit_options_markup
    )


# Меняем название события
@edit_event_router.callback_query(F.data.startswith("edit_name_"))
async def edit_event_name(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.answer(
        "✏️ Введите новое название события:"
    )

    await state.update_data(event_id=event_id)  # Сохраняем event_id для редактирования
    await state.set_state(EditEventStates.editing_name)


@edit_event_router.message(EditEventStates.editing_name)
async def save_new_event_name(message: types.Message, state: FSMContext):
    db = next(get_db())
    data = await state.get_data()
    event_id = data.get("event_id")

    event = db.query(Event).filter_by(id=event_id).first()
    if event:
        event.name = message.text
        db.commit()
        await message.answer("✅ Название события успешно обновлено!", reply_markup=markup)
    else:
        await message.answer("❗ Событие не найдено.")

    await state.clear()


# Меняем адрес события
@edit_event_router.callback_query(F.data.startswith("edit_address_"))
async def edit_event_name(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.answer(
        "✏️ Введите новый адрес события:"
    )
    await state.update_data(event_id=event_id)  # Сохраняем event_id для редактирования
    await state.set_state(EditEventStates.editing_address)


@edit_event_router.message(EditEventStates.editing_address)
async def save_new_event_name(message: types.Message, state: FSMContext):
    db = next(get_db())
    data = await state.get_data()
    event_id = data.get("event_id")

    event = db.query(Event).filter_by(id=event_id).first()
    if event:
        address = message.text
        coordinates = get_location_by_address(address)
        if not coordinates:
            await message.reply("Не удалось определить местоположение по введенному адресу\n Попробуйте еще раз")
            return
        else:
            event.address = message.text
            db.commit()
            await message.answer("✅ Адрес события успешно обновлено!", reply_markup=markup)
    else:
        await message.answer("❗ Событие не найдено.")

    await state.clear()


# Меняем цену события
@edit_event_router.callback_query(F.data.startswith("edit_price_"))
async def edit_event_name(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.answer(
        "✏️ Введите новую цену события:"
    )
    await state.update_data(event_id=event_id)  # Сохраняем event_id для редактирования
    await state.set_state(EditEventStates.editing_price)


@edit_event_router.message(EditEventStates.editing_price)
async def save_new_event_name(message: types.Message, state: FSMContext):
    db = next(get_db())
    data = await state.get_data()
    event_id = data.get("event_id")

    try:
        event = db.query(Event).filter_by(id=event_id).first()
        if event:
            event.price = int(message.text)
            db.commit()
            await message.answer("✅ Цена события обновлена!", reply_markup=markup)
        else:
            await message.answer("❗ Событие не найдено.")

        await state.clear()
    except Exception as e:
        await message.answer("Произошла ошибка при изменений цены. Проверьте правильность данных")
        logging.info(f"Ошибка в edit_event: {e}")


# Меняем описание события
@edit_event_router.callback_query(F.data.startswith("edit_desc_"))
async def edit_event_name(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.answer(
        "✏️ Введите новое описание события:"
    )
    await state.update_data(event_id=event_id)  # Сохраняем event_id для редактирования
    await state.set_state(EditEventStates.editing_desc)


@edit_event_router.message(EditEventStates.editing_desc)
async def save_new_event_name(message: types.Message, state: FSMContext):
    db = next(get_db())
    data = await state.get_data()
    event_id = data.get("event_id")

    try:
        event = db.query(Event).filter_by(id=event_id).first()
        if event:
            event.description = message.text
            db.commit()
            await message.answer("✅ Описание события обновлено!", reply_markup=markup)
        else:
            await message.answer("❗ Событие не найдено.")

        await state.clear()
    except Exception as e:
        await message.answer("Произошла ошибка при изменений описания. Проверьте правильность данных")
        logging.info(f"Ошибка в edit_event: {e}")


# Меняем время события
@edit_event_router.callback_query(F.data.startswith("edit_time_"))
async def edit_event_name(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.answer(
        "✏️ Введите новую время и дату события:\n"
        "Формат ввода ДД/ММ/ГГГГ ЧЧ:ММ"
    )
    await state.update_data(event_id=event_id)  # Сохраняем event_id для редактирования
    await state.set_state(EditEventStates.editing_time)


@edit_event_router.message(EditEventStates.editing_time)
async def save_new_event_name(message: types.Message, state: FSMContext):
    db = next(get_db())
    data = await state.get_data()
    event_id = data.get("event_id")

    try:
        event = db.query(Event).filter_by(id=event_id).first()
        if event:
            event.event_time = message.text
            db.commit()
            await message.answer("✅ Время события обновлено!", reply_markup=markup)
        else:
            await message.answer("❗ Событие не найдено.", reply_markup=markup)

        await state.clear()
    except Exception as e:
        await message.answer("Произошла ошибка при изменений времени. Проверьте правильность данных")
        logging.info(f"Ошибка в edit_event: {e}")


