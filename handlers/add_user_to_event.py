import html
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import asc

from db.database import get_db, User, Registration, Event
from utils.split_message import split_message

manual_register_user_router = Router()


class ManualRegistration(StatesGroup):
    waiting_for_user_id = State()


@manual_register_user_router.callback_query(F.data.startswith("add_user_to_event_"))
async def add_user_to_event_start(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])

    with get_db() as db:
        event = db.query(Event).filter_by(id=event_id).first()
        if not event:
            await callback.message.answer("Событие не найдено.")
            return

        if event.current_participants >= event.max_participants:
            await callback.message.answer("На это событие больше нет мест.")
            return

    await state.update_data(event_id=event_id)
    kb = InlineKeyboardBuilder()
    kb.button(text="Вывести список пользователей и ID", callback_data="show_users_id")
    await callback.message.answer(
        "Введите ID пользователя, которого хотите добавить на событие:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(ManualRegistration.waiting_for_user_id)


@manual_register_user_router.callback_query(F.data == "show_users_id")
async def show_users_ids(callback: types.CallbackQuery, state: FSMContext):
    with get_db() as db:
        all_users = (
            db.query(User)
            .filter_by(is_registered=True)
            .order_by(asc(User.first_name), asc(User.last_name))
            .all()
        )

    user_list = "\n".join(
        f"▪️ {html.escape(user.first_name or '')} {html.escape(user.last_name or '')} — ID: <code>{user.id}</code>"
        for user in all_users
    ) or "Нет зарегистрированных пользователей."

    for chunk in split_message(user_list):
        await callback.message.answer(chunk, parse_mode="HTML")

    await callback.message.answer("Введите ID пользователя, которого хотите добавить:")
    await state.set_state(ManualRegistration.waiting_for_user_id)


@manual_register_user_router.message(ManualRegistration.waiting_for_user_id)
async def process_user_id_for_event(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
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

        if not user.is_registered:
            await message.answer("Этот пользователь не завершил регистрацию в боте.")
            await state.clear()
            return

        if event.current_participants >= event.max_participants:
            await message.answer("На это событие больше нет мест.")
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
        user.user_games += 1

        first_name = html.escape(user.first_name or "")
        last_name = html.escape(user.last_name or "")
        event_name = html.escape(event.name or "")
        event_time = event.event_time.strftime("%d.%m.%Y %H:%M") if event.event_time else "-"

        await message.answer(
            f"✅ Пользователь <b>{first_name} {last_name}</b> добавлен.\n"
            f"Событие: <b>{event_name}</b>\n"
            f"Дата: <b>{event_time}</b>\n"
            f"Участников: <b>{event.current_participants}/{event.max_participants}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Назад в админку", callback_data="admin_panel")
            ]]),
            parse_mode="HTML"
        )

    await state.clear()


@manual_register_user_router.callback_query(F.data.startswith("invite_"))
async def generate_invite_link(callback: types.CallbackQuery):
    flask_base_url = "http://109.73.201.136:8000/"
    event_id = callback.data.split("_")[1]

    flask_url = f"{flask_base_url}/event/{event_id}/add-participants"
    kb = InlineKeyboardBuilder()
    kb.button(text="Перейти в форму заполнения", url=flask_url)
    await callback.message.answer("🌐 Добавление участников к событию:", reply_markup=kb.as_markup())
