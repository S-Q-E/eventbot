from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, types, F
from db.database import get_db, Event, Registration

delete_event_router = Router()

main_menu_btn = InlineKeyboardButton(text="Назад",
                                     callback_data="admin_panel")
markup = InlineKeyboardMarkup(inline_keyboard=[[main_menu_btn]])


async def event_action_markup(event_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_event_{event_id}"),
                InlineKeyboardButton(text="✏️Редактировать", callback_data=f"edit_event_{event_id}")
            ],
            [
                InlineKeyboardButton(text="➕ Добавить участника", callback_data=f"add_user_to_event_{event_id}"),
                InlineKeyboardButton(text="➕ Добавить команду", callback_data=f"invite_{event_id}"),
                InlineKeyboardButton(text="➖ Удалить участника", callback_data=f"manual_deleting_{event_id}")
            ],
            [
                InlineKeyboardButton(text="↩️ Назад", callback_data="admin_panel")
            ]
        ]
    )


@delete_event_router.callback_query(F.data == "delete_event_button")
@delete_event_router.callback_query(F.data.startswith("delete_page_"))
async def delete_event(callback_query: types.CallbackQuery):
    try:
        page = int(callback_query.data.split("_")[-1])
    except ValueError:
        page = 1

    db = next(get_db())
    events = db.query(Event).order_by(Event.event_time.asc()).all()

    if not events:
        await callback_query.message.answer("Нет доступных событий.")
        return

    total_pages = (len(events) + 3 - 1) // 3
    page = max(1, min(page, total_pages))
    events_to_show = events[(page - 1) * 3:page * 3]

    for event in events_to_show:
        await callback_query.message.answer(
            f"🔹 <b>{event.name}</b>\n"
            f"{event.event_time}\n",
            reply_markup=await event_action_markup(event_id=event.id),
            parse_mode="HTML"
        )

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="⬅️ Предыдущая", callback_data=f"delete_page_{page - 1}")
        )
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="Следующая ➡️", callback_data=f"delete_page_{page + 1}")
        )
    pagination_markup = InlineKeyboardMarkup(inline_keyboard=[pagination_buttons])
    await callback_query.message.answer(f"Страница {page}/{total_pages}", reply_markup=pagination_markup)


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
        db.query(Registration).filter_by(event_id=event_id).delete()
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

