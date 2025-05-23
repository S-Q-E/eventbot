import logging
from datetime import datetime
from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import get_db, Event, Category
from handlers.delete_event import event_action_markup
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
    editing_max_participants = State()
    edit_category = State()


@edit_event_router.callback_query(F.data.startswith("edit_event_"))
async def edit_event(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[-1])
    edit_options_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"edit_name_{event_id}")],
            [InlineKeyboardButton(text="📍 Адрес", callback_data=f"edit_address_{event_id}")],
            [InlineKeyboardButton(text="🕒 Время", callback_data=f"edit_time_{event_id}")],
            [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_price_{event_id}")],
            [InlineKeyboardButton(text="🏐 Категория", callback_data=f"set_category_{event_id}")],
            [InlineKeyboardButton(text="🗓 Описание", callback_data=f"edit_desc_{event_id}")],
            [InlineKeyboardButton(text="↕️Количество участников", callback_data=f"edit_participants_{event_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_delete_event_button_{event_id}")]
        ]
    )
    await callback_query.message.edit_text(
        "<b>Выберите, что хотите редактировать</b>:",
        reply_markup=edit_options_markup
    )


@edit_event_router.callback_query(F.data.startswith("back_to_delete_event_button_"))
async def back_to_edit_list(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[-1])
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()

    if not event:
        await callback.message.answer("Событие не найдено!", show_alert=True)
        return

    await callback.message.edit_text(
            f"🔹 <b>{event.name}</b>\n"
            f"{event.event_time}\n",
            reply_markup=await event_action_markup(event_id=event.id),
            parse_mode="HTML"
    )


# Меняем название события
@edit_event_router.callback_query(F.data.startswith("edit_name_"))
async def edit_event_name(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.reply(
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
    await callback_query.message.reply(
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


@edit_event_router.callback_query(F.data.startswith("edit_participants_"))
async def edit_max_participants(callback_query: CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[-1])
    with next(get_db()) as db:
        event = db.query(Event).filter(Event.id == event_id).first()
        await callback_query.message.answer(f"✏️Введите количество участников события.\n Текущее количество {event.max_participants}")
        db.close()
    await state.update_data(event_id=event_id)
    await state.set_state(EditEventStates.editing_max_participants)


@edit_event_router.message(EditEventStates.editing_max_participants)
async def edit_max_participants(message: Message, state: FSMContext):
    with next(get_db()) as db:
        data = await state.get_data()
        event_id = int(data.get("event_id"))
        try:
            event = db.query(Event).filter(Event.id == event_id).first()
            event.max_participants = message.text
            db.commit()
            await message.answer("✅ Изменения успешно сохранены! ", reply_markup=markup)
        except Exception as e:
            logging.info(f"Ошибка в хэндлере edit_max_participants\n Код ошибки: {e}")
            await message.answer("⚠️Произошла ошибка. Повторите снова", reply_markup=markup)
        finally:
            db.close()


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
            event.event_time = datetime.strptime(message.text, '%d/%m/%Y %H:%M')

            db.commit()
            await message.answer("✅ Время события обновлено!", reply_markup=markup)
        else:
            await message.answer("❗ Событие не найдено.", reply_markup=markup)

        await state.clear()
    except Exception as e:
        await message.answer("Произошла ошибка при изменений времени. Проверьте правильность данных")
        logging.info(f"Ошибка в edit_event: {e}")


@edit_event_router.callback_query(F.data.startswith("set_category_"))
async def set_event_category(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    with next(get_db()) as db:
        try:
            categories = db.query(Category).order_by(Category.name).all()
            kb = InlineKeyboardBuilder()
            for category in categories:
                kb.button(
                    text=category.name,
                    callback_data=f"setting_category_{category.id}"
                )
            await callback.message.answer("Выберите категорию", reply_markup=kb.as_markup())
            await state.update_data(event_id=event_id)
            await state.set_state(EditEventStates.edit_category)
        except Exception as e:
            logging.info(f"Ошибка в set_event_category {e}")
            await callback.message.answer("Неизвестная ошибка")
        finally:
            db.close()


@edit_event_router.callback_query(EditEventStates.edit_category)
async def edit_event_category(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data.split("_")[-1]
    data = await state.get_data()
    event_id = data.get("event_id")
    kb = InlineKeyboardBuilder()
    kb.button(text="Назад", callback_data="admin_panel")
    with next(get_db()) as db:
        try:
            event = db.query(Event).filter_by(id=event_id).first()
            if not event:
                await callback.message.answer("Событие не найдено")
            else:
                event.category_id = category_id
                db.commit()
                await callback.message.answer("Категория события обновлена!", reply_markup=kb.as_markup())
        except Exception as e:
            await callback.message.answer("Ошибка при изменений категории")
            logging.info(f"Ошибка в dit_event_category {e}")
        finally:
            db.close()
