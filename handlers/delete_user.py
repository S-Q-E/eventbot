from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.database import get_db, User

delete_user_router = Router()


# Хэндлер для вывода списка пользователей
@delete_user_router.callback_query(F.data == "all_users")
async def list_registered_users(callback: types.CallbackQuery):
    db = next(get_db())

    try:
        # Запрашиваем всех пользователей
        users = db.query(User).all()

        if not users:
            await callback.message.answer("Нет пользователей для отображения.")
            return

        # Отправляем отдельное сообщение для каждого пользователя
        for user in users:
            status_emoji = "✅" if user.is_registered else "❌"
            user_info = (
                f"{status_emoji} {user.first_name} {user.last_name}\n"
                f"Username: @{user.username or 'Нет'}"
            )

            # Кнопка для удаления конкретного пользователя
            delete_button = InlineKeyboardButton(
                text="Удалить пользователя",
                callback_data=f"delete_user_{user.id}"
            )
            markup = InlineKeyboardMarkup(inline_keyboard=[[delete_button]])

            await callback.message.answer(text=user_info, reply_markup=markup)

    except Exception as e:
        await callback.message.answer("Произошла ошибка при получении списка пользователей.")
        print(f"Ошибка при запросе пользователей: {e}")
    finally:
        db.close()


# Хэндлер для удаления пользователя
@delete_user_router.callback_query(F.data.startswith("delete_user_"))
async def delete_user(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[-1])
    db = next(get_db())

    try:
        # Находим и удаляем пользователя
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await callback.message.answer("Пользователь не найден.")
            return

        db.delete(user)
        db.commit()

        await callback.answer(f"Пользователь {user.first_name} удалён.", show_alert=True)
        await callback.message.edit_text(f"Пользователь {user.first_name} удален.")

    except Exception as e:
        await callback.answer("Ошибка при удалении пользователя.")
        print(f"Ошибка удаления пользователя: {e}")
    finally:
        db.close()
