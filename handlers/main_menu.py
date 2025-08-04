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

    events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
    admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
    user_profile = InlineKeyboardButton(text="👤 Мой профиль", callback_data="user_profile")
    user_stats = InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="user_stats")
    user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                         [admin_panel], [user_profile], [user_stats], [user_help]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_profile], [user_stats], [user_help]])
    if user:
        if user.is_admin:
            await message.answer(f"Привет, <b>{user.first_name} {user.last_name}!</b>\n\n"
                                 f"✅ Это приложение для участников спортивных событий\n"
                                 f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                 reply_markup=admin_markup)
        else:
            await message.answer(f"Привет, <b>{user.first_name} {user.last_name}!</b>\n\n"
                                 f"✅ Это приложение для участников спортивных событий\n"
                                 f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                 reply_markup=reg_user_markup)
    else:
        await message.answer(f"Привет, <b>{user.first_name} {user.last_name}!</b>\n\n"
                             f"✅ Это приложение для участников спортивных событий\n"
                             f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n")


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

    events_button = InlineKeyboardButton(text="💬 Доступные события", callback_data="events_list")
    admin_panel = InlineKeyboardButton(text="😎 Панель админа", callback_data="admin_panel")
    user_profile = InlineKeyboardButton(text="👤 Мой профиль", callback_data="user_profile")
    user_stats = InlineKeyboardButton(text="📊 Статистика пользователей", callback_data="user_stats")
    user_help = InlineKeyboardButton(text="🆘 Помощь", callback_data="user_help")

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button],
                                                         [admin_panel], [user_profile], [user_stats], [user_help]])

    reg_user_markup = InlineKeyboardMarkup(inline_keyboard=[[events_button], [user_profile], [user_stats], [user_help]])
    if user:
        if user.is_admin:
            await callback.message.answer(f"Привет, <b>{user.first_name} {user.last_name}!</b>\n\n"
                                          f"✅ Это приложение для участников спортивных событий\n"
                                          f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                          reply_markup=admin_markup)
        else:
            await callback.message.answer(f"Привет, <b>{user.first_name} {user.last_name}!</b>\n\n"
                                          f"✅ Это приложение для участников спортивных событий\n"
                                          f"✅ Здесь вы найдете подходящее занятие для себя, выбрав локацию и время.\n",
                                          reply_markup=reg_user_markup)
    else:
        await callback.message.answer(f"{callback.message.from_user.username}\n\n"
                                      f"<b>Вы не прошли регистрацию\n"
                                      f"Пожалуйста пройдите регистрацию</b?>")


@main_menu_router.callback_query(F.data == "user_stats")
async def user_statistics(callback: types.CallbackQuery):
    """
    Показывает статистику пользователей по количеству сыгранных матчей
    """
    user_id = callback.from_user.id
    db = next(get_db())
    
    try:
        # Получаем всех пользователей, отсортированных по количеству игр
        users = db.query(User).filter(User.user_games > 0).order_by(User.user_games.desc()).all()
        
        if not users:
            await callback.message.answer("📊 Пока нет статистики игр. Участвуйте в событиях!")
            return
        
        # Получаем текущего пользователя
        current_user = db.query(User).filter_by(id=user_id).first()
        
        # Формируем топ-10
        stats_text = "📊 <b>Топ игроков по количеству матчей:</b>\n\n"
        
        medals = ["👑", "🥈", "🥉"]
        
        for i, user in enumerate(users[:10], 1):
            games_text = "матч" if user.user_games == 1 else "матчей"
            if i <= 3:
                stats_text += f"{medals[i-1]}{user.first_name} {user.last_name} {user.user_games} {games_text}\n"
            else:
                stats_text += f"{i}. {user.first_name} {user.last_name} {user.user_games} {games_text}\n"
        
        # Проверяем, есть ли текущий пользователь в топ-10
        current_user_position = None
        for i, user in enumerate(users, 1):
            if user.id == user_id:
                current_user_position = i
                break
        
        # Если пользователь не в топ-10, показываем его позицию
        if current_user_position and current_user_position > 10:
            current_user_games = current_user.user_games if current_user else 0
            games_text = "матч" if current_user_games == 1 else "матчей"
            stats_text += f"\n{current_user_position}. Вы {current_user_games} {games_text}"
        
        # Добавляем кнопку возврата
        back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        markup = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
        
        await callback.message.answer(stats_text, reply_markup=markup)
        
    except Exception as e:
        logging.error(f"Ошибка при получении статистики пользователей: {e}")
        await callback.message.answer("Произошла ошибка при получении статистики. Попробуйте позже.")
    finally:
        db.close()
