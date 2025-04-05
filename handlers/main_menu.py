import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User

main_menu_router = Router()


@main_menu_router.message(Command("main_menu"))
async def main_menu(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """

    user_id = message.from_user.id
    db = next(get_db())

    try:
        user = db.query(User).filter_by(id=user_id).first()
    except Exception as e:
        await message.answer(f"Произошла ошибка при доступе к базе данных. Попробуйте позже. {e}")

        return

    events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_page_1")
    admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
    user_profile = InlineKeyboardButton(text="👤 Мой профиль", callback_data="user_profile")
    user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                         [admin_panel], [user_profile], [user_help]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_profile], [user_help]])
    if user:
        if user.is_admin:
            await message.answer(f"Привет, {user.first_name} {user.last_name}!\n"
                                 f"✅ Это приложение для участников спортивных событий\n"
                                 f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                 reply_markup=admin_markup)
        else:
            await message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                                 f"<b>Добро пожаловать! {message.from_user.username}</b>\n",
                                 reply_markup=reg_user_markup)
    else:
        await message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                             f"<b>Добро пожаловать!</b>\n\n"
                             f"<b> Вы не прошли регистрацию </b>\n"
                             f"<b> Пожалуйста пройдите регистрацию </b>")


@main_menu_router.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """

    user_id = callback.from_user.id
    db = next(get_db())

    try:
        user = db.query(User).filter_by(id=user_id).first()
    except Exception as e:
        await callback.message.answer("Произошла ошибка при доступе к базе данных. Попробуйте позже.")
        logging.info(f"Ошибка в main_menu: {e}")
        return

    events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_page_1")
    admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
    user_profile = InlineKeyboardButton(text="👤 Мой профиль", callback_data="user_profile")
    user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                         [admin_panel], [user_profile], [user_help]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_profile], [user_help]])
    if user:
        if user.is_admin:
            await callback.message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                                          f"<b>Добро пожаловать! {callback.from_user.username}</b>\n",
                                          reply_markup=admin_markup)
        else:
            await callback.message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                                          f"<b>Добро пожаловать! {callback.from_user.username}</b>\n",
                                          reply_markup=reg_user_markup)
    else:
        await callback.message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                                      f"<b>Вы не прошли регистрацию\n"
                                      f"Пожалуйста пройдите регистрацию</b?>")
