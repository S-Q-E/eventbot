from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy import asc

from db.database import get_db, User, Event, Registration

manual_register_user_router = Router()


class RegisterUserToEvent(StatesGroup):
    wait_user_id = State()
    wait_event_id = State()


@manual_register_user_router.callback_query(F.data.startswith("add_user_to_event_"))
async def start_register_user_to_event(callback: types.CallbackQuery, state: FSMContext):
    """
    Старт регистрации пользователя на событие.
    """
    event_id = int(callback.data.split("_")[-1])
    await callback.message.answer("Введите ID пользователя, которого нужно зарегистрировать на событие:")
    with next(get_db()) as db:
        all_users = db.query(User).filter_by(is_registered = True).order_by(asc(User.first_name), asc(User.last_name)).all()
        user_list = "\n".join(
            f"▪️{user.first_name} {user.last_name} ID: <code> {user.id} </code>" for user in all_users
        ) or "Нет участников"
        await callback.message.answer(f"Список пользователей\n{user_list}")
    await state.update_data(event_id=event_id)
    await state.set_state(RegisterUserToEvent.wait_user_id)


@manual_register_user_router.message(RegisterUserToEvent.wait_user_id)
async def register_user_to_event(message: types.Message, state: FSMContext):
    """
    Регистрация пользователя на событие.
    """
    user_id = message.text

    if not user_id.isdigit():
        await message.answer("ID пользователя должен быть число. Повторите ввод:")
        return

    with next(get_db()) as db:

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            await message.answer("Пользователь с таким номером телефона не найден. Попробуйте снова.")
            return

        if not user.is_registered:
            await message.answer("Этот пользователь не зарегистрирован в системе. Сначала завершите регистрацию.")
            return

        data = await state.get_data()
        user_id = user.id
        event_id = data.get("event_id")

        event = db.query(Event).filter(Event.id == int(event_id)).first()

        if not event:
            await message.answer("Событие с таким ID не найдено. Попробуйте снова.")
            return

        if event.current_participants >= event.max_participants:
            await message.answer("На это событие больше нет мест. Выберите другое.")
            return

        existing_registration = db.query(Registration).filter(
            Registration.user_id == user_id,
            Registration.event_id == int(event_id)
        ).first()

        if existing_registration:
            await message.answer("Пользователь уже зарегистрирован на это событие.")
            return

        new_registration = Registration(
            user_id=user_id,
            event_id=int(event_id),
            reminder_time=None,
            is_paid=True
        )
        event.current_participants += 1
        db.add(new_registration)
        db.commit()

        back_btn = InlineKeyboardButton(text="Назад", callback_data="admin_panel")
        markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
        await message.answer(
            f"✅ Пользователь {user.first_name} {user.last_name} зарегистрирован на событие <b>{event.name}</b>!",
            reply_markup=markup
        )
        db.close()
        await state.clear()
