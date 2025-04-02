import logging
import os
from aiogram import types, Router, F
from aiogram.types import InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.database import User, Event, Registration, get_db, VotingSession
from utils.mvp_poll import announce_winner

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")

vote_router = Router()


# @vote_router.callback_query(F.data == 'start_vote')
# async def start_voting(callback: types.CallbackQuery):
#     """
#     Обработчик команды для начала голосования.
#     Извлекает всех пользователей с is_mvp_candidate==True,
#     отправляет их фото (или дефолтное) и прикрепляет инлайн-клавиатуру с кнопками для голосования.
#     :param callback:
#     :return:
#     """
#     db = next(get_db())
#     try:
#         candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
#         if not candidates:
#             await callback.message.answer("Нет кандидатов на голосование")
#         media = []
#         keyboard_builder = InlineKeyboardBuilder()
#         for candidate in candidates:
#             display_name = f"🏆 {candidate.first_name} {candidate.last_name} ({candidate.votes})"
#             photo = candidate.photo_file_id
#             media.append(InputMediaPhoto(media=photo, caption=display_name))
#             keyboard_builder.button(
#                 text=display_name,
#                 callback_data=f"vote_{candidate.id}"
#             )
#
#         await callback.message.answer_media_group(media=media)
#
#         # Отправляем отдельное сообщение с инлайн-клавиатурой для голосования
#         keyboard_builder.adjust(1)  # Устанавливаем количество кнопок в ряду
#         await callback.message.answer("Выберите кандидата для голосования:", reply_markup=keyboard_builder.as_markup())
#     except Exception as e:
#         logging.info(f"Ошибка в start_voting {e}")
#         await callback.message.answer("Ошибка попробуйте позднее")
#         db.close()
#     finally:
#         db.close()

@vote_router.poll()
async def handle_poll(poll: types.Poll):
    db = next(get_db())
    try:
        # Получение последнего активного голосования
        voting_session = db.query(VotingSession).order_by(VotingSession.id.desc()).first()
        if not voting_session or voting_session.poll_id != poll.id:
            return

        # Обновление количества голосов для каждого кандидата
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        for i, option in enumerate(poll.options):
            if i < len(candidates):
                candidates[i].votes = option.voter_count
        db.commit()

    except Exception as e:
        logging.error(f"Ошибка при обновлении результатов опроса: {e}")
        db.rollback()
    finally:
        db.close()


# @vote_router.callback_query(F.data.startswith("vote_"))
# async def handle_vote_callback(callback: types.CallbackQuery):
#     candidate_id = int(callback.data.split("_")[1])
#     db: Session = next(get_db())
#     try:
#         # Получаем кандидата и увеличиваем количество голосов
#         candidate = db.query(User).filter(User.id == candidate_id).first()
#         if candidate:
#             candidate.votes += 1
#             db.commit()
#             candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
#             keyboard_builder = InlineKeyboardBuilder()
#             for cand in candidates:
#                 display_name = f"🏆 {cand.first_name} {cand.last_name} ({cand.votes})"
#                 keyboard_builder.button(
#                     text=display_name,
#                     callback_data=f"vote_{cand.id}"
#                 )
#             keyboard_builder.adjust(1)
#             await callback.bot.edit_message_reply_markup(chat_id=CHAT_ID,
#                                                          message_id=callback.message.message_id,
#                                                          reply_markup=keyboard_builder.as_markup())
#         else:
#             await callback.answer("Кандидат не найден.")
#     except Exception as e:
#         logging.error(f"Ошибка при обработке голосования: {e}")
#         await callback.answer("Произошла ошибка. Попробуйте позже.")
#         db.rollback()
#     finally:
#         db.close()
#
#
# @vote_router.callback_query(F.data == "end_voting")
# async def end_voting_handler(callback: types.CallbackQuery):
#     """
#     Обработчик команды для завершения голосования.
#     Определяет победителя и отправляет поздравление в группу.
#     """
#     winner_name, photo_id = announce_winner()
#     if winner_name and photo_id:
#         await callback.message.answer_photo(photo=photo_id,
#                                             caption=f"Звание лучшего игрока недели получает\n"
#                                                     f" 🏆{winner_name} 🏆 \nПоздравляем!🎉🎉🎉")
#     else:
#         logging.info("Не удалось определить победителя")
