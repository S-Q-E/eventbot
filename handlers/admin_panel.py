from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.check_admin import check_admin_rights

admin_router = Router()


@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    is_admin = await check_admin_rights(callback.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="Создать событие", callback_data="create_event")],
        [InlineKeyboardButton(text="Удалить событие", callback_data="delete_event_button")],
        [InlineKeyboardButton(text="Назначить админа", callback_data="set_admin")],
        [InlineKeyboardButton(text="Подписчики бота", callback_data="user_list")],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    if is_admin:
        await callback.message.answer("Панель админа. Здесь вы можете создавать и удалять события\n"
                                      "А также назначать админов и смотреть пользователей бота", reply_markup=markup)
    else:
        await callback.message.answer("У вас нет доступа к этой панели.\n"
                                      "Обратитесь к админу бота для увеличения привилегий")