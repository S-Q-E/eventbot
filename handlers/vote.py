import logging

from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.database import User, Event, Registration, get_db

vote_router = Router()


@vote_router.callback_query(F.data == 'start_vote')
async def start_voting(callback: types.CallbackQuery):
    """
    Обработчик команды для начала голосования.
    Извлекает всех пользователей с is_mvp_candidate==True,
    отправляет их фото (или дефолтное) и прикрепляет инлайн-клавиатуру с кнопками для голосования.
    :param callback: 
    :return: 
    """
    db = next(get_db())
    try:
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        if not candidates:
            await callback.message.answer("Нет кандидатов на голосование")
        media = []
        keyboard_builder = InlineKeyboardBuilder()
        for candidate in candidates:
            display_name = candidate.username or candidate.first_name or "Без имени"
            photo = candidate.photo_file_id
            media.append(InputMediaPhoto(media=photo, caption=display_name))
            keyboard_builder.button(
                text=display_name,
                callback_data=f"vote_{candidate.id}"
            )

        await callback.message.answer_media_group(media=media)

        # Отправляем отдельное сообщение с инлайн-клавиатурой для голосования
        keyboard_builder.adjust(1)  # Устанавливаем количество кнопок в ряду
        await callback.message.answer("Выберите кандидата для голосования:", reply_markup=keyboard_builder.as_markup())
    except Exception as e:
        logging.info(f"Ошибка в start_voting {e}")
        await callback.message.answer("Ошибка попробуйте позднее")
        db.close()
    finally:
        db.close()