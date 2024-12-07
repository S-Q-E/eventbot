import logging
from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User, Event, Registration
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

delete_user_from_event_router = Router()


class DeleteUser(StatesGroup):
    wait_user_phone = State()


@delete_user_from_event_router.callback_query(F.data.startswith("manual_deleting"))
async def get_user_phone(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ID пользователя которого нужно удалить.\n")
    event_id = int(callback.data.split("_")[-1])
    with next(get_db()) as db:
        participants = db.query(User).join(Registration, User.id == Registration.user_id) \
            .filter(Registration.event_id == event_id).all()
        participants_list = "\n".join(
            f"Список пользователей: \n"
            f"▪️{user.first_name} {user.last_name} ID: {user.id}" for user in participants
        ) or "Нет участников"
        await callback.message.answer(participants_list)
        db.close()
    await state.update_data(event_id=event_id)
    await state.set_state(DeleteUser.wait_user_phone)


@delete_user_from_event_router.message(DeleteUser.wait_user_phone)
async def delete_user_from_event(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.text
    event_id = data.get("event_id")
    if not user_id.isdigit():
        await message.answer("Неверный формат ID. Повторите попытку")
        return

    try:
        with next(get_db()) as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                await message.answer("Такого пользователя нет в базе данных.")

            event = db.query(Event).filter(Event.id == event_id).first()

            existing_registration = db.query(Registration).filter(
                Registration.user_id == user.id,
                Registration.event_id == int(event_id)
            ).first()
            if not existing_registration:
                await message.answer("Пользователь не зарегистрирован на это событие")
                return

            event.current_participants -= 1
            db.delete(existing_registration)
            db.commit()
            back_btn = InlineKeyboardButton(text="Назад", callback_data="delete_event_button")
            markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
            await message.answer(f"Запись участника {user.first_name} {user.last_name} на событие {event.name} отменена!", reply_markup=markup)
            db.close()
        await state.clear()
    except Exception as e:
        logging.info(f"Ошибка в delete_user_from_event: {e}")
        await message.answer("Произошла ошибка в базе данных. Попробуйте еще раз")
    finally:
        db.close()





