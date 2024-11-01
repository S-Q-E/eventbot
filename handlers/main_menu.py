from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# from utils.reg_required import registration_required
from db.database import get_db, User

main_menu_router = Router()


# @registration_required
@main_menu_router.message(Command("main_menu"))
@main_menu_router.callback_query(F.data == "main_menu")
async def main_menu(message: types.Message):
    """
    Функция приветствия. При старте бота предлагается выбрать опцию
    """

    user_id = message.from_user.id
    db = next(get_db())

    try:
        user = db.query(User).filter_by(id=user_id).first()
    except Exception as e:
        await message.answer("Произошла ошибка при доступе к базе данных. Попробуйте позже.")

        return

    create_event = InlineKeyboardButton(text="🎉 Создать event", callback_data="create_event")
    events_button = InlineKeyboardButton(text="💬 Доступные event-ы", callback_data="events")
    my_events_button = InlineKeyboardButton(text="📆 Мои записи", callback_data="my_events")
    user_list_botton = InlineKeyboardButton(text="❤ Подписчики бота", callback_data="user_list")
    add_admin_button = InlineKeyboardButton(text="😎 Добавить админа", callback_data="set_admin")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button],
                                                         [create_event], [user_list_botton],
                                                         [add_admin_button]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [my_events_button]])
    if user:
        if user.is_admin:
            await message.answer("*******EVENTBOT********\n\n"
                                 f"<b>Добро пожаловать! {message.from_user.username}</b>\n", reply_markup=admin_markup)
        else:
            await message.answer("*******EVENTBOT********\n\n"
                                 f"<b>Добро пожаловать! {message.from_user.username}</b>\n", reply_markup=reg_user_markup)
    else:
        await message.answer("*******EVENTBOT********\n\n"
                             f"<b>Вы не прошли регистрацию\n"
                             f"Пожалуйста пройдите регистрацию</b?>")
