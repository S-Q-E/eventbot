import logging

from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.database import User, Event, Registration, get_db
from utils.prepare_poll import announce_winner

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
            display_name = f"🏆 {candidate.first_name} {candidate.last_name} ({candidate.votes})"
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


@vote_router.callback_query(F.data.startswith("vote_"))
async def handle_vote_callback(callback: types.CallbackQuery):
    candidate_id = int(callback.data.split("_")[1])
    db: Session = next(get_db())
    try:
        # Получаем кандидата и увеличиваем количество голосов
        candidate = db.query(User).filter(User.id == candidate_id).first()
        if candidate:
            candidate.votes += 1
            db.commit()
            candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
            keyboard_builder = InlineKeyboardBuilder()
            for cand in candidates:
                display_name = f"🏆 {cand.first_name} {cand.last_name} ({cand.votes})"
                keyboard_builder.button(
                    text=display_name,
                    callback_data=f"vote_{cand.id}"
                )
            keyboard_builder.adjust(1)
            # Редактируем сообщение с новой клавиатурой
            await callback.message.edit_reply_markup(reply_markup=keyboard_builder.as_markup())
            await callback.answer(f"Ваш голос учтен за {candidate.first_name}!")
        else:
            await callback.answer("Кандидат не найден.")
    except Exception as e:
        logging.error(f"Ошибка при обработке голосования: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")
        db.rollback()
    finally:
        db.close()


@vote_router.callback_query(F.data == "end_voting")
async def end_voting_handler(callback: types.CallbackQuery):
    """
    Обработчик команды для завершения голосования.
    Определяет победителя и отправляет поздравление в группу.
    """
    winner_name, photo_id = announce_winner()
    if winner_name and photo_id:
        await callback.message.answer_photo(photo=photo_id,
                                            caption=f"Звание лучшего игрока недели получает"
                                                    f" 🏆{winner_name} 🏆 Поздравляем!🎉🎉🎉")
    else:
        logging.info("Не удалось определить победителя")
