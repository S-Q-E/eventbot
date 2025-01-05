from aiogram import types, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

help_router = Router()


@help_router.callback_query(F.data == "user_help")
async def help_message(callback: CallbackQuery):
    back_btn = InlineKeyboardButton(text="Назад", callback_data="main_menu")
    markup = InlineKeyboardMarkup(inline_keyboard=[[back_btn]])
    await callback.message.answer("""📝 Как записаться на событие: 1. Выберите событие из списка\n 
    2. Нажмите кнопку «Записаться» ✅.\n
    3. Оплатите участие по СБП, нажмите на кнопку проверить платеж.\n
    4. Подтвердите выбор времени напоминания ⏰ (за день или за 2 часа до начала).\n
    Поздравляю! Вы смогли записаться на желаемое событие.\n Вам придет уведомление в заданноe
    время. Спасибо, что пользуетесь нашим Ботом!\n\n"
    "Нажмите кнопку  <u>'Подробнее'</u> для просмотра комментариев к событию и другой информации.""", reply_markup=markup)

