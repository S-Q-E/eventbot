from aiogram import Router,types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from db.database import get_db, Event
from utils.get_coordinates import get_location_by_address

send_loc_router = Router()


@send_loc_router.callback_query(F.data.startswith("show_on_map_"))
async def send_event_loc(callback: types.CallbackQuery):
    try:
        event_id = int(callback.data.split("show_on_map_")[1])
    except (ValueError, IndexError):
        await callback.message.answer("ID события не найден.")
        return

    # Получаем событие из базы данных
    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    if not event:
        await callback.message.answer("Событие не найдено.")
        return

    # Получаем координаты по адресу события
    coordinates = get_location_by_address(event.address)
    if coordinates:
        latitude, longitude = coordinates
        await callback.message.answer_location(latitude=latitude, longitude=longitude)
    else:
        # Отправляем ссылку на Google Maps, если координаты не найдены
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={event.address.replace(' ', '+')}"
        await callback.message.answer(
            f"Не удалось найти точное местоположение.\n"
            f"Попробуйте открыть адрес в Google Maps: [Открыть карту]({google_maps_url})",
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    await callback.answer()
