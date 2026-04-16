import logging
import html
from aiogram import Router, types, F
from db.database import get_db, User, Registration, Event
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

manual_register_user_router = Router()


class ManualRegistration(StatesGroup):
    waiting_for_user_id = State()


@manual_register_user_router.callback_query(F.data.startswith("add_user_to_event_"))
async def add_user_to_event_start(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(event_id=event_id)
    await callback.message.answer("Введите ID пользователя, которого хотите добавить на событие:")
    await state.set_state(ManualRegistration.waiting_for_user_id)


@manual_register_user_router.message(ManualRegistration.waiting_for_user_id)
async def process_user_id_for_event(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный числовой ID.")
        return

    user_id = int(message.text)
    data = await state.get_data()
    event_id = data.get("event_id")

    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        event = db.query(Event).filter_by(id=event_id).first()

        if not user or not event:
            await message.answer("Пользователь или событие не найдены.")
            await state.clear()
            return

        existing_reg = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()
        if existing_reg:
            await message.answer("Пользователь уже зарегистрирован на это событие.")
            await state.clear()
            return

        new_reg = Registration(user_id=user_id, event_id=event_id, is_paid=True)
        db.add(new_reg)
        event.current_participants += 1
        # db.commit() automatic
        
        first_name = html.escape(user.first_name or "")
        last_name = html.escape(user.last_name or "")
        event_name = html.escape(event.name or "")
        
        await message.answer(f"Пользователь <b>{first_name} {last_name}</b> успешно добавлен на событие <b>{event_name}</b>.",
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                 InlineKeyboardButton(text="Назад в админку", callback_data="admin_panel")
                             ]]))
    await state.clear()
