from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from utils.check_admin import check_admin_rights
from utils.user_report import generate_user_report

admin_router = Router()


@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    is_admin = await check_admin_rights(callback.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="Создать событие", callback_data="create_event")],
        [InlineKeyboardButton(text="Редактировать событие", callback_data="delete_event_button")],
        [InlineKeyboardButton(text="Добавить нового пользователя", callback_data="add_user")],
        [InlineKeyboardButton(text="Удалить пользователя", callback_data="all_users")],
        [InlineKeyboardButton(text="Редактировать пользователя", callback_data="edit_user")],
        [InlineKeyboardButton(text="Настройки админа", callback_data="set_admin")],
        [InlineKeyboardButton(text="Отправить сообщения пользователям", callback_data="send_to_users")],
        [InlineKeyboardButton(text="Сгенерировать отчет", callback_data="report")],
        [InlineKeyboardButton(text="Просмотреть аватары пользователей", callback_data="show_users_avatar")],
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


@admin_router.callback_query(F.data == "admin_help")
async def admin_help_message(callback: types.CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_panel")

        ]
    ])
    await callback.message.answer("<b> Справка </b>\n"
                                  "🔹 <code>Создание события </code> - для создания разных событий\n"
                                  "🔹 <code>Редактировать событие </code> - возможность редактировать событие,"
                                  "а также добавлять и удалять участников на это событие\n"
                                  "🔹 <code>Добавить нового пользователя</code> - ручное добавление несуществующих"
                                  " в Телеграм пользователей\n"
                                  "🔹 <code>Настройки админа</code> - управление правами админа\n"
                                  "🔹 <code>Подписчики бота </code> - список всех зарегистрированных пользователей\n"
                                  "🔹 <code>Незарег. пользователи</code> - список всех пользователей когда-либо "
                                  "запускавших бота\n "
                                  "🔹 <code>Сгенерировать отчет</code> - генерация Excel файла с данными о "
                                  "пользователях\n", reply_markup=markup)


@admin_router.callback_query(F.data == "report")
async def send_report(callback: types.CallbackQuery):
    file_name = generate_user_report()
    report = FSInputFile(file_name)
    await callback.message.answer("Ваш отчет сгенерирован!")
    await callback.message.answer_document(report)


