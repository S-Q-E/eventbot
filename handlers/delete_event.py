from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, types, F
from db.database import get_db, Event

delete_event_router = Router()

main_menu_btn = InlineKeyboardButton(text="Назад",
                                     callback_data="admin_panel")
markup = InlineKeyboardMarkup(inline_keyboard=[[main_menu_btn]])


@delete_event_router.callback_query(F.data == "delete_event_button")
async def delete_event(callback_query: types.CallbackQuery):
    db = next(get_db())
    events = db.query(Event).all()
    if events:
        for event in events:
            await callback_query.message.answer(
                f"🎉 <b>{event.name}</b>\n"
                f"🕒 Дата: {event.event_time.strftime('%d/%m/ %H:%M')}\n",
                reply_markup=await event_deletion_markup(event.id),
                parse_mode="HTML"
            )
    else:
        await callback_query.message.answer("Нет доступных событий для удаления.")


@delete_event_router.callback_query(F.data.startswith("delete_event_"))
async def confirm_delete_event(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[-1])

    # Запросим подтверждение перед удалением
    confirm_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_delete_{event_id}"),
            InlineKeyboardButton(text="🚫 Отменить", callback_data="cancel_delete")
        ]
    ])

    await callback_query.message.answer(
        "Вы уверены, что хотите удалить это событие?",
        reply_markup=confirm_markup
    )


@delete_event_router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_event(callback_query: types.CallbackQuery):
    await callback_query.message.edit_reply_markup()
    event_id = int(callback_query.data.split("_")[-1])
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    if event:
        db.delete(event)
        db.commit()
        await callback_query.message.answer("Событие успешно удалено.", reply_markup=markup)
    else:
        await callback_query.message.answer("Событие не найдено или уже удалено.", reply_markup=markup)


@delete_event_router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("Удаление отменено.", reply_markup=markup)


async def event_deletion_markup(event_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Удалить",
                    callback_data=f"delete_event_{event_id}"
                )
            ]
        ]
    )