import os
import logging
import asyncio
from aiogram import Router, Bot, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.database import get_db, User, Registration
from utils.get_nearest_events import get_nearest_event

message_router = Router()


class AdminBroadcast(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
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
    await message.answer("Отправьте фото которое хотите прикрепить к сообщению")
    await state.set_state(AdminBroadcast.waiting_for_photo)


@message_router.message(AdminBroadcast.waiting_for_photo, F.photo)
async def admin_input_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)

    data = await state.get_data()
    admin_text = data["message_text"]

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Подтвердить", callback_data="admin_confirm")
    keyboard.button(text="Редактировать текст", callback_data="admin_edit")
    keyboard.button(text="Подтвердить и протестировать", callback_data="send_to_admins")
    keyboard.adjust(2)

    await message.answer_photo(
        photo=photo_id,
        caption=f"Предпросмотр сообщения:\n\n{admin_text}\n\nПодтвердите или отредактируйте:",
        reply_markup=keyboard.as_markup()
    )
    await state.set_state(AdminBroadcast.waiting_for_confirmation)


@message_router.callback_query(F.data.in_(["admin_confirm", "admin_edit", "send_to_admins"]))
async def admin_confirmation(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == "admin_edit":
        await callback.message.answer("Введите текст сообщения заново:")
        await state.set_state(AdminBroadcast.waiting_for_text)
        await callback.answer("Редактирование")
        return
    elif callback.data == "send_to_admins":
        await callback.answer("Начинаю рассылку...")
        db = next(get_db())
        sent_count = 0

        data = await state.get_data()
        admin_text = data["message_text"]
        photo_id = data["photo_id"]  # ← file_id фото

        # Формируем разметку для кнопок
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Да, я планирую", callback_data="events_list")
        keyboard.button(text="Нет, не смогу", callback_data="cannot_attend")
        keyboard.adjust(2)
        broadcast_markup = keyboard.as_markup()

        try:
            event = await get_nearest_event()
            admins = db.query(User).filter(User.is_admin).all()

            for user in admins:
                try:
                    user_id = int(user.id)
                except (ValueError, TypeError):
                    logging.error(f"Невалидный user_id: {user.id}")
                    continue

                # Пропускаем уже записавшихся на ближайшее событие
                if db.query(Registration).filter_by(user_id=user_id, event_id=event.id).first():
                    continue

                try:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=photo_id,
                        caption=admin_text,
                        reply_markup=broadcast_markup
                    )
                    sent_count += 1
                except TelegramForbiddenError as e:
                    logging.info(f"Пользователь {user.id} {user.first_name, user.last_name} заблокировал бота")
                    continue
            await callback.message.answer(f"Рассылка завершена: отправлено {sent_count} сообщений.")
        except Exception as e:
            logging.exception(f"Ошибка в рассылке: {e}")
            await callback.message.answer("Не удалось выполнить рассылку.")
        finally:
            db.close()
            await state.clear()
    elif callback.data == "admin_confirm":
        await callback.answer("Начинаю рассылку...")
        db = next(get_db())
        sent_count = 0

        data = await state.get_data()
        admin_text = data["message_text"]
        photo_id = data["photo_id"]  # ← file_id фото

        # Формируем разметку для кнопок
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Да, я планирую", callback_data="events_list")
        keyboard.button(text="Нет, не смогу", callback_data="cannot_attend")
        keyboard.adjust(2)
        broadcast_markup = keyboard.as_markup()

        try:
            event = await get_nearest_event()
            users = db.query(User).filter(User.is_registered == True).all()

            for user in users:
                try:
                    user_id = int(user.id)
                except (ValueError, TypeError):
                    logging.error(f"Невалидный user_id: {user.id}")
                    continue

                # Пропускаем уже записавшихся на ближайшее событие
                if db.query(Registration).filter_by(user_id=user_id, event_id=event.id).first():
                    continue

                try:
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=photo_id,
                        caption=admin_text,
                        reply_markup=broadcast_markup
                    )
                    sent_count += 1
                except TelegramForbiddenError as e:
                    logging.info(f"Пользователь {user.id} {user.first_name, user.last_name} заблокировал бота")
                    continue
            await callback.message.answer(f"Рассылка завершена: отправлено {sent_count} сообщений.")
        except Exception as e:
            logging.exception(f"Ошибка в рассылке: {e}")
            await callback.message.answer("Не удалось выполнить рассылку.")
        finally:
            db.close()
            await state.clear()


@message_router.callback_query(F.data == "cannot_attend")
async def user_cannot_attend(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Хорошо, будем рады видеть тебя на следующую игру.")
    await callback.answer()
