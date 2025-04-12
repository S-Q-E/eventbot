import os
import logging
import asyncio
from aiogram import Router, Bot, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.database import get_db, User, Registration
from utils.get_nearest_events import get_nearest_event

message_router = Router()


class AdminBroadcast(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()


@message_router.callback_query(F.data == "send_to_users")
async def send_to_users_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("Введите текст сообщения:")
    await state.set_state(AdminBroadcast.waiting_for_text)
    await callback.answer()


@message_router.message(AdminBroadcast.waiting_for_text)
async def admin_input_message(message: types.Message, state: FSMContext):
    admin_text = message.text.strip()
    if not admin_text:
        await message.answer("Сообщение не может быть пустым. Введите текст:")
        return
    await state.update_data(message_text=admin_text)

    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="Подтвердить", callback_data="admin_confirm")
    keyboard_builder.button(text="Редактировать", callback_data="admin_edit")
    keyboard_builder.adjust(2)

    preview_text = f"Предпросмотр сообщения:\n\n{admin_text}\n\nПодтвердите или отредактируйте:"
    await message.answer(preview_text, reply_markup=keyboard_builder.as_markup())
    await state.set_state(AdminBroadcast.waiting_for_confirmation)


@message_router.callback_query(F.data.in_(["admin_confirm", "admin_edit"]))
async def admin_confirmation(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    admin_text = data.get("message_text", "").strip()

    if callback.data == "admin_edit":
        await callback.message.answer("Введите текст сообщения заново:")
        await state.set_state(AdminBroadcast.waiting_for_text)
        await callback.answer("Редактирование")
        return

    elif callback.data == "admin_confirm":
        await callback.answer("Сообщение подтверждено. Начинается рассылка.")
        db = next(get_db())
        sent_count = 0
        try:
            event = await get_nearest_event()
            users = db.query(User).filter(User.is_registered == True).all()
            keyboard_builder = InlineKeyboardBuilder()
            keyboard_builder.button(text="да, я планирую", callback_data=f"events_page_1")
            keyboard_builder.button(text="нет, я не смогу", callback_data="cannot_attend")
            keyboard_builder.adjust(2)
            broadcast_markup = keyboard_builder.as_markup()

            for user in users:
                try:
                    user_id = int(user.id)
                except (ValueError, TypeError):
                    logging.error(f"Некорректный user id для пользователя: {user}")
                    continue
                try:
                    reg = db.query(Registration).filter_by(user_id=user_id, event_id=event.id).first()
                    if reg:
                        continue

                    await bot.send_message(chat_id=user_id, text=admin_text, reply_markup=broadcast_markup)
                    sent_count += 1
                except Exception as e:
                    logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
                    continue

            await callback.message.answer(f"Сообщения отправлены {sent_count} пользователям.")
        except Exception as e:
            logging.exception(f"Ошибка при рассылке сообщений: {e}")
            await callback.message.answer("Ошибка при рассылке сообщений.")
        finally:
            db.close()
            await state.clear()


@message_router.callback_query(F.data == "cannot_attend")
async def user_cannot_attend(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Хорошо, будем рады видеть тебя на следующую игру.")
    await callback.answer()
