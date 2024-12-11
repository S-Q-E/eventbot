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
    user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                         [admin_panel], [user_help]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_help]])
    if user:
        if user.is_admin:
            await message.answer("🎉🎉🎉🎉🎉 EVENTBOT 🎉🎉🎉🎉🎉\n\n"
                                 f"<b>Добро пожаловать!</b> {message.from_user.username}\n",
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

        return

    events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_page_1")
    admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
    user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                         [admin_panel], [user_help]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_help]])
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
