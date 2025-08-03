from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import Session, joinedload

from db.database import get_db, User
from utils.check_admin import check_admin_rights
from utils.user_report import generate_user_report

admin_router = Router()


@admin_router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    is_admin = await check_admin_rights(callback.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="Создать событие", callback_data="create_event")],
        [InlineKeyboardButton(text="Редактировать событие", callback_data="delete_event_button")],
        [InlineKeyboardButton(text="Добавить нового пользователя", callback_data="add_user")],
        [InlineKeyboardButton(text="Удалить пользователя", callback_data="all_users")],
        [InlineKeyboardButton(text="Редактировать пользователя", callback_data="edit_user")],
        [InlineKeyboardButton(text="Настройки админа", callback_data="set_admin")],
        [InlineKeyboardButton(text="Отправить сообщения пользователям", callback_data="send_to_users")],
        [InlineKeyboardButton(text="Отправить личное сообщение", callback_data="send_priv_message")],
        [InlineKeyboardButton(text="Изменить уровень игрока", callback_data="change_users_level")],
        [InlineKeyboardButton(text="Сгенерировать отчет", callback_data="report")],
        [InlineKeyboardButton(text="Просмотреть аватары пользователей", callback_data="show_users_avatar")],
        [InlineKeyboardButton(text="Просмотреть интересы пользователей", callback_data="view_user_subscriptions")],
        [InlineKeyboardButton(text="Редактировать интересы пользователей", callback_data="edit_user_interests")],
        [InlineKeyboardButton(text="Отправить логи", callback_data="send_logs")],
        [InlineKeyboardButton(text="Справка", callback_data="admin_help")],
        [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    sec_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Главное меню", callback_data="main_menu")
    ]])
    if is_admin:
        await callback.message.edit_text(f"<b>Добро пожаловать {callback.message.from_user.username}</b>\n",
                                         reply_markup=markup)
    else:
        await callback.message.edit_text("У вас нет доступа к этой панели.\n"
                                         "Обратитесь к админу бота для увеличения привилегий", reply_markup=sec_markup)


@admin_router.callback_query(F.data == "admin_help")
async def admin_help_message(callback: types.CallbackQuery):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Назад", callback_data="admin_panel")

        ]
    ])
    await callback.message.edit_text("<b> Справка </b>\n"
                                     "🔹 <code>Создание события </code> - для создания разных событий\n"
                                     "🔹 <code>Редактировать событие </code> - возможность редактировать событие,"
                                     "а также добавлять и удалять участников на это событие\n"
                                     "🔹 <code>Добавить нового пользователя</code> - ручное добавление несуществующих"
                                     " в Телеграм пользователей\n"
                                     "🔹 <code>Настройки админа</code> - управление правами админа\n"
                                     "🔹 <code>Подписчики бота </code> - список всех зарегистрированных пользователей\n"
                                     "🔹 <code>Незарег. пользователи</code> - список всех пользователей когда-либо "
                                     "запускавших бота\n "
                                     "🔹 <code>Сгенерировать отчет</code> - генерация Excel файла с данными о "
                                     "пользователях\n", reply_markup=markup)


@admin_router.callback_query(F.data == "report")
async def send_report(callback: types.CallbackQuery):
    file_name = generate_user_report()
    report = FSInputFile(file_name)
    await callback.message.answer("Ваш отчет сгенерирован!")
    await callback.message.answer_document(report)


@admin_router.callback_query(F.data == "send_logs")
async def send_logs(callback: types.CallbackQuery):
    try:
        with open("bot.log", "r") as f:
            lines = f.readlines()[-20:]  # последние 50 строк
            log_chunk = "".join(lines)
            await callback.message.answer(f"<pre>{log_chunk}</pre>")
    except Exception as e:
        await callback.message.answer(f"Ошибка при чтении логов: {e}")


@admin_router.callback_query(F.data == "view_user_subscriptions")
async def view_user_subscriptions(callback: types.CallbackQuery):
    db: Session = next(get_db())
    users = db.query(User).options(joinedload(User.interests)).all()
    db.close()

    messages = []
    batch = []
    max_message_length = 4000
    current_length = 0

    for user in users:
        username = user.username or f"{user.first_name} {user.last_name}"
        interests = ", ".join([cat.name for cat in user.interests]) or "Нет подписок"
        user_info = f"👤 <b>{username}</b>\n📌 Подписки: {interests}\n\n"
        if current_length + len(user_info) > max_message_length:
            messages.append("".join(batch))
            batch = [user_info]
            current_length = len(user_info)
        else:
            batch.append(user_info)
            current_length += len(user_info)

    if batch:
        messages.append("".join(batch))

    for msg in messages:
        await callback.message.answer(msg)

    # Кнопка «Назад»
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="admin_panel")
    await callback.message.answer("Выберите действие:", reply_markup=keyboard.as_markup())
    await callback.answer()

class ChangeUserLevel(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_level_choice = State()

# 1. Вывод списка игроков
@admin_router.callback_query(F.data == "change_users_level")
async def change_users_level_start(callback: types.CallbackQuery, state: FSMContext):
    db: Session = next(get_db())
    users = db.query(User).all()
    db.close()

    max_msg_length = 3800
    batch, messages, current_length = [], [], 0

    for user in users:
        username = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Без имени"
        user_info = f"🧑‍💼 <b>{username}</b> | 🆔 <code>{user.id}</code>\n"
        if current_length + len(user_info) > max_msg_length:
            messages.append("".join(batch))
            batch = [user_info]
            current_length = len(user_info)
        else:
            batch.append(user_info)
            current_length += len(user_info)
    if batch:
        messages.append("".join(batch))

    for msg in messages:
        await callback.message.answer(msg)

    await callback.message.answer(
        "✏️ Введите <b>ID</b> пользователя (скопируйте из списка выше), чей уровень хотите изменить:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
            ]
        )
    )
    await state.set_state(ChangeUserLevel.waiting_for_user_id)
    await callback.answer()


# 2. Получение id пользователя и показ выбора уровня
@admin_router.message(ChangeUserLevel.waiting_for_user_id)
async def ask_for_level(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "⚠️ Введите корректный числовой ID.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                ]
            )
        )
        return

    user_id = int(message.text)
    db: Session = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        await message.answer(
            "❌ Пользователь не найден. Попробуйте еще раз.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                ]
            )
        )
        return

    await state.update_data(user_id=user_id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌱 Новичок", callback_data="set_level:Новичок")],
            [InlineKeyboardButton(text="🏅 Любитель", callback_data="set_level:Любитель")],
            [InlineKeyboardButton(text="👑 Профи", callback_data="set_level:Профи")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="change_users_level")],
        ]
    )
    await message.answer(
        f"Выберите новый уровень для <b>{user.first_name or ''} {user.last_name or ''}</b> (🆔 <code>{user.id}</code>):",
        reply_markup=kb
    )
    await state.set_state(ChangeUserLevel.waiting_for_level_choice)


# 3. Обработка выбора уровня
@admin_router.callback_query(ChangeUserLevel.waiting_for_level_choice, F.data.startswith("set_level:"))
async def set_user_level(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    level = callback.data.split(":", 1)[1]

    db: Session = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        old_level = user.user_level or "Не установлен"
        user.user_level = level
        db.commit()
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        await callback.message.answer(
            f"✅ Уровень игрока <b>{name}</b> (🆔 <code>{user.id}</code>) "
            f"успешно изменён с <b>{old_level}</b> на <b>{level}</b>! 🎉",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад в админ-панель", callback_data="admin_panel")]
                ]
            )
        )
    else:
        await callback.message.answer("❌ Пользователь не найден.",
                                     reply_markup=InlineKeyboardMarkup(
                                         inline_keyboard=[
                                             [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                                         ]
                                     ))
    db.close()
    await state.clear()
    await callback.answer()


# 4. Обработка кнопки "назад" из любого состояния FSM
@admin_router.callback_query(F.data == "admin_panel")
async def back_to_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    # тут можно повторить вывод панели или просто ответить кнопкой
    await callback.message.answer(
        "🔙 Возврат в админ-панель.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
    )
    await callback.answer()