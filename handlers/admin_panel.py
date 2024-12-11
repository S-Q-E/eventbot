from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.check_admin import check_admin_rights

admin_router = Router()


@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    is_admin = await check_admin_rights(callback.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="Создать событие", callback_data="create_event")],
        [InlineKeyboardButton(text="Редактировать событие", callback_data="delete_event_button")],
        [InlineKeyboardButton(text="Добавить нового пользователя", callback_data="add_user")],
        [InlineKeyboardButton(text="Настройки админа", callback_data="set_admin")],
        [InlineKeyboardButton(text="Подписчики бота", callback_data="user_list")],
        [InlineKeyboardButton(text="Незарегистрированные пользователи", callback_data="all_users")],
        [InlineKeyboardButton(text="Сгенерировать отчет", callback_data="report")],
        [InlineKeyboardButton(text="Справка", callback_data="admin_help")],
        [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    sec_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
    ]])
    if is_admin:
        await callback.message.edit_text(f"<b>Добро пожаловать {callback.message.from_user.username}</b>\n",
                                         reply_markup=markup)
    else:
        await callback.message.edit_text("У вас нет доступа к этой панели.\n"
                                         "Обратитесь к админу бота для увеличения привилегий", reply_markup=sec_markup)
