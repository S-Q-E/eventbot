from aiogram import Router,types, F
from aiogram.types import InlineKeyboardButton

from db.database import get_db, Event
from utils.get_coordinates import get_coordinates

send_loc_router = Router()


@send_loc_router.callback_query(F.data.startswith("show_on_map_"))
async def send_event_loc(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    try:
        event_id = int(callback.data.split("show_on_map_")[1])
    except (ValueError, IndexError) as ex:
        await callback.message.answer("ID ивента не найдено")
        return

    db = next(get_db())
    event = db.query(Event).filter_by(id=event_id).first()
    if event and event.address:
        latitude, longitude = get_coordinates(event.address)
        if latitude is not None and longitude is not None:
            # Успешно получены координаты
            url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            await callback.message.answer(f"Местоположение события:\n{url}")
        else:
            # Ошибка при получении координат
            await callback.message.answer("Не удалось получить координаты по указанному адресу. Пожалуйста, проверьте "
                                          "адрес события.")
    else:
        main_menu_btn = InlineKeyboardButton(
            text="Главное меню",
            callback_data="main_menu"
        )
        await callback.message.answer("Адрес события отсутствует.")







