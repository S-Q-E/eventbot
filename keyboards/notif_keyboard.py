from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_notification_keyboard(event_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="За день", callback_data=f"notify_24h_{event_id}")],
        [InlineKeyboardButton(text="За 2 часа", callback_data=f"notify_2h_{event_id}")]
    ])

    return keyboard
