import html
from aiogram import Router, types, F
from db.database import get_db, User, Registration, Event
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


delete_user_from_event_router = Router()


class ManualDeleting(StatesGroup):
    waiting_for_user_id = State()


@delete_user_from_event_router.callback_query(F.data.startswith("manual_deleting_"))
async def delete_user_from_event_start(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(event_id=event_id)

    with get_db() as db:
        registered_user_ids = [
            row[0]
            for row in db.query(Registration.user_id)
            .filter_by(event_id=event_id)
            .order_by(Registration.user_id)
            .all()
        ]

    await callback.message.answer("Введите ID пользователя, которого хотите удалить из события:")

    if registered_user_ids:
        users_text = "\n".join(f"<code>{user_id}</code>" for user_id in registered_user_ids)
        await callback.message.answer(
            "Пользователи, записанные на событие (ID):\n"
            f"{users_text}"
        )
    else:
        await callback.message.answer("На это событие пока никто не записан.")
    await state.set_state(ManualDeleting.waiting_for_user_id)


@delete_user_from_event_router.message(ManualDeleting.waiting_for_user_id)
async def process_user_id_for_delete(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректный числовой ID.")
        return

    user_id = int(message.text)
    data = await state.get_data()
    event_id = data.get("event_id")

    with get_db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        event = db.query(Event).filter_by(id=event_id).first()
        registration = db.query(Registration).filter_by(user_id=user_id, event_id=event_id).first()

        if not registration:
            await message.answer("Пользователь не зарегистрирован на это событие.")
            await state.clear()
            return

        db.delete(registration)
        if event and event.current_participants > 0:
            event.current_participants -= 1
        # db.commit() automatic

        first_name = html.escape(user.first_name if user else "Неизвестный")
        last_name = html.escape(user.last_name if user else "")
        event_name = html.escape(event.name if event else "Неизвестное событие")

        await message.answer(
            f"Пользователь <b>{first_name} {last_name}</b> успешно удален из события <b>{event_name}</b>.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="Назад в админку", callback_data="admin_panel")
                ]]
            ),
        )
    await state.clear()
