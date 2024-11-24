import datetime
import io
from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from db.database import get_db, Registration, Event, User
from utils.parse_user_bill import parse_receipt

NAME = "Василий Романович К."

event_join_router = Router()


class EventRegistration(StatesGroup):
    waiting_for_check = State()


@event_join_router.callback_query(F.data.startswith("join_"))
async def handle_receipt_upload(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    try:
        event_id = int(callback_query.data.split("join_")[1])
    except (IndexError, ValueError):
        await callback_query.message.answer("Ошибка: неверный формат данных события.")
        return
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    await state.update_data(event_id=event.id)
    await state.set_state(EventRegistration.waiting_for_check)
    await callback_query.message.answer(f"Для записи нужно оплатить {event.price} P. \n"
                                        f"Если у вас СБЕР: перевод на номер +77785856188\n"
                                        f"Для клиентов других банков: 4444 4444 4444 4477")


@event_join_router.message(EventRegistration.waiting_for_check)
async def check_payment(message: types.Message, state: FSMContext):
    # Получаем сохраненные данные (event_id)
    data = await state.get_data()
    event_id = data.get("event_id")

    # Открываем изображение чека
    photo = message.photo[-1]
    photo_file = await message.bot.download(file=photo, destination=io.BytesIO())
    photo_file.seek(0)

    # Получаем доступ к базе данных и пользователю
    db = next(get_db())
    user_id = message.from_user.id
    event = db.query(Event).filter_by(id=event_id).first()
    user = db.query(User).filter_by(id=user_id).first()

    if not event or not user:
        await message.answer("Событие или пользователь не найдены.")
        return

    # Ожидаемые данные для проверки
    expected_amount = event.price

    # Вызываем функцию парсинга и проверки
    is_valid = await parse_receipt(photo_file.getvalue(), expected_amount, NAME)

    if is_valid:
        # Записываем пользователя на событие
        new_registration = Registration(user_id=user_id, event_id=event.id, is_paid=True)
        db.add(new_registration)
        event.current_participants += 1
        db.commit()

        # Завершаем состояние
        await state.clear()

        await message.answer("Оплата подтверждена! Вы успешно записаны на событие.")
    else:
        await message.answer("Не удалось подтвердить чек. Проверьте данные и попробуйте снова.")
