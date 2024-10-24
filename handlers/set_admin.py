from aiogram import Router, types
from db.database import get_db, User
from aiogram.filters import Command
from aiogram.types import Message

admin_settings_router = Router()

@admin_settings_router.message(Command("admin_settings"))
async def admin_set(message:Message, callback_query):
    pass

@admin_settings_router.message(Command(commands="add_admin"))
async def add_admin(message: Message):
    db = next(get_db())

    # Проверяем, является ли вызывающий пользователь администратором
    calling_user = db.query(User).filter_by(id=message.from_user.id).first()
    if not calling_user or not calling_user.is_admin:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    # Получаем ID пользователя, которого нужно сделать администратором
    try:
        user_id = int(message.get_args())  # Например, команда будет выглядеть как /add_admin 123456
    except ValueError:
        await message.answer("Пожалуйста, укажите корректный ID пользователя.")
        return

    # Ищем пользователя в базе данных
    user_to_promote = db.query(User).filter_by(id=user_id).first()

    if user_to_promote:
        # Делаем пользователя администратором
        user_to_promote.is_admin = True
        db.commit()

        await message.answer(f"Пользователь {user_to_promote.username} теперь является администратором!")
    else:
        await message.answer("Пользователь с таким ID не найден.")


@admin_settings_router.message(Command(commands="remove_admin"))
async def remove_admin(message: Message):
    db = next(get_db())

    calling_user = db.query(User).filter_by(id=message.from_user.id).first()
    if not calling_user or not calling_user.is_admin:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        user_id = int(message.get_args())
    except ValueError:
        await message.answer("Пожалуйста, укажите корректный ID пользователя.")
        return

    user_to_demote = db.query(User).filter_by(id=user_id).first()

    if user_to_demote:
        if not user_to_demote.is_admin:
            await message.answer(f"Пользователь {user_to_demote.username} не является администратором.")
            return

        user_to_demote.is_admin = False
        db.commit()

        await message.answer(f"Пользователь {user_to_demote.username} больше не является администратором.")
    else:
        await message.answer("Пользователь с таким ID не найден.")
