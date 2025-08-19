from sqlalchemy import func
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import logging
from db.database import User, Registration, Event, get_db


def get_top_users(db, period: str):
    """
    Возвращает топ пользователей по количеству оплаченных игр
    period = "month" | "all"
    """
    now = datetime.utcnow()
    query = (
        db.query(
            User.id,
            User.first_name,
            User.last_name,
            func.count(Registration.id).label("games")
        )
        .join(Registration, Registration.user_id == User.id)
        .filter(Registration.is_paid == True)
    )

    if period == "month":
        month_ago = now - timedelta(days=30)
        query = query.join(Event, Registration.event_id == Event.id).filter(Event.event_time >= month_ago)

    return (
        query.group_by(User.id)
        .order_by(func.count(Registration.id).desc())
        .all()
    )


async def send_stats(callback, period: str):
    db = next(get_db())
    try:
        users = get_top_users(db, period)

        if not users:
            await callback.message.answer("📊 Пока нет статистики игр. Участвуйте в событиях!")
            return

        # Заголовок
        titles = {
            "month": "📊 <b>Топ игроков за месяц:</b>\n\n",
            "all": "📊 <b>Топ игроков за всё время:</b>\n\n",
        }
        stats_text = titles.get(period, titles["all"])

        medals = ["👑", "🥈", "🥉"]

        for i, user in enumerate(users[:10], 1):
            games_text = "матч" if user.games == 1 else "матчей"
            if i <= 3:
                stats_text += f"{medals[i-1]} {user.first_name} {user.last_name} — {user.games} {games_text}\n"
            else:
                stats_text += f"{i}. {user.first_name} {user.last_name} — {user.games} {games_text}\n"

        # Текущий пользователь
        user_id = callback.from_user.id
        current_user_position = None
        current_user_games = 0
        for i, user in enumerate(users, 1):
            if user.id == user_id:
                current_user_position = i
                current_user_games = user.games
                break

        if current_user_position and current_user_position > 10:
            games_text = "матч" if current_user_games == 1 else "матчей"
            stats_text += f"\n{current_user_position}. Вы — {current_user_games} {games_text}"

        # Кнопки переключения
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗓 За месяц", callback_data="user_stats_month"),
                InlineKeyboardButton(text="∞ Всё время", callback_data="user_stats_all"),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])

        await callback.message.edit_text(stats_text, reply_markup=markup)

    except Exception as e:
        logging.error(f"Ошибка при получении статистики: {e}")
        await callback.message.answer("Произошла ошибка при получении статистики. Попробуйте позже.")
    finally:
        db.close()


