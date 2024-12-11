from aiogram import types, F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


admin_help_router = Router()


@admin_help_router.callback_query(F.data == "admin_help")
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