import logging
import html
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User
from utils.user_stats_view import send_stats

main_menu_router = Router()


@main_menu_router.message(Command("main_menu"))
async def main_menu_cmd(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """
    user_id = message.from_user.id
    with get_db() as db:
        try:
            user = db.query(User).filter_by(id=user_id).first()
        except Exception as e:
            await message.answer(f"Произошла ошибка при доступе к базе данных. Попробуйте позже.")
            logging.error(f"Ошибка в main_menu: {e}")
            return

        events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
        admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
        user_profile = InlineKeyboardButton(text="👤 Мой профиль", callback_data="user_profile")
        user_stats = InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="user_stats")
        user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

        admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                             [admin_panel], [user_profile], [user_stats], [user_help]])

        reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_profile], [user_stats], [user_help]])
        
        if user:
            first_name = html.escape(user.first_name or "")
            last_name = html.escape(user.last_name or "")
            if user.is_admin:
                await message.answer(f"Привет, <b>{first_name} {last_name}!</b>\n\n"
                                     f"✅ Это приложение для участников спортивных событий\n"
                                     f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                     reply_markup=admin_markup)
            else:
                await message.answer(f"Привет, <b>{first_name} {last_name}!</b>\n\n"
                                     f"✅ Это приложение для участников спортивных событий\n"
                                     f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                     reply_markup=reg_user_markup)
        else:
            await message.answer(f"Привет!\n\n"
                                 f"✅ Это приложение для участников спортивных событий\n"
                                 f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n"
                                 f"Пожалуйста, пройдите регистрацию /start")


@main_menu_router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """
    user_id = callback.from_user.id
    with get_db() as db:
        try:
            user = db.query(User).filter_by(id=user_id).first()
        except Exception as e:
            await callback.message.answer("Произошла ошибка при доступе к базе данных. Попробуйте позже.")
            logging.info(f"Ошибка в main_menu: {e}")
            return

        events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
        admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
        user_profile = InlineKeyboardButton(text="👤 Мой профиль", callback_data="user_profile")
        user_stats = InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="user_stats")
        user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

        admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                             [admin_panel], [user_profile], [user_stats], [user_help]])

        reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_profile], [user_stats], [user_help]])
        
        if user:
            first_name = html.escape(user.first_name or "")
            last_name = html.escape(user.last_name or "")
            if user.is_admin:
                await callback.message.answer(f"Привет, <b>{first_name} {last_name}!</b>\n\n"
                                              f"✅ Это приложение для участников спортивных событий\n"
                                              f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                              reply_markup=admin_markup)
            else:
                await callback.message.answer(f"Привет, <b>{first_name} {last_name}!</b>\n\n"
                                              f"✅ Это приложение для участников спортивных событий\n"
                                              f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                              reply_markup=reg_user_markup)
        else:
            await callback.message.answer(f"<b>Вы не прошли регистрацию\n"
                                          f"Пожалуйста пройдите регистрацию /start</b>")


@main_menu_router.callback_query(F.data == "user_stats")
async def user_stats_entry(callback: types.CallbackQuery):
    await send_stats(callback, "all")


@main_menu_router.callback_query(F.data == "user_stats_month")
async def user_stats_month(callback: types.CallbackQuery):
    await send_stats(callback, "month")


@main_menu_router.callback_query(F.data == "user_stats_all")
async def user_stats_all(callback: types.CallbackQuery):
    await send_stats(callback, "all")
