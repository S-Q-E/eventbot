from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from db.database import get_db, Event, Registration


async def send_mvp_links(bot: Bot):
    """
    Проверяет события, у которых прошло 2 часа от начала, и отправляет участникам ссылку на опрос.
    Предполагается, что у модели Event можно добавить флаг (например, is_mvp_sent) для предотвращения повторной отправки.
    Если такого флага нет, можно добавить дополнительную логику по идентификации.
    """
    db_gen = get_db()
    db = next(db_gen)
    now = datetime.now()
    # Получаем события, у которых event_time + 2 часа <= now.
    # Если добавлен флаг, можно добавить условие, что опрос ещё не отправлялся.
    events = db.query(Event).filter(Event.event_time <= now - timedelta(hours=2)).all()

    for event in events:
        # Получаем всех зарегистрированных участников события
        registrations = db.query(Registration).filter(Registration.event_id == event.id).all()
        for reg in registrations:
            # Формируем ссылку на мини-приложение с параметрами event_id и user_id
            link = f"https://e0f4-2a03-32c0-6002-5d39-d8d1-3abe-17a-1643.ngrok-free.app/mvp?event_id={event.id}&user_id={reg.user_id}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="Проголосовать за MVP",
                    web_app=WebAppInfo(url=link)
                )
            ]])
            try:
                # Отправляем сообщение с кнопкой WebApp
                await bot.send_message(
                    chat_id=reg.user_id,
                    text=f"Прошло 2 часа с начала матча <b>{event.name}</b>! Пройдите опрос за MVP.",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Не удалось отправить ссылку пользователю {reg.user_id}: {e}")
        # Если хотите, можно обновить событие, установив флаг отправки опроса, чтобы не слать повторно.
        # event.is_mvp_sent = True
        # db.commit()

    db.close()
    # Закрываем генератор сессии
    try:
        next(db_gen)
    except StopIteration:
        pass

