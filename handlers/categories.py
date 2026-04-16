import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import Category, get_db

category_router = Router()


class CategoryStates(StatesGroup):
    waiting_for_name = State()


@category_router.callback_query(F.data == "add_category")
async def cmd_add_cat(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название новой категории:")
    await state.set_state(CategoryStates.waiting_for_name)


@category_router.message(CategoryStates.waiting_for_name)
async def process_add_cat(msg: Message, state: FSMContext):
    name = msg.text.strip()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="К категориям", callback_data="manage_category")
    keyboard.adjust(1)
    markup = keyboard.as_markup()
    try:
        with get_db() as db:
            if db.query(Category).filter_by(name=name).first():
                await msg.answer("Категория с таким именем уже есть.")
            else:
                db.add(Category(name=name))
                # db.commit() is automatic
                await msg.answer(f"Категория «{name}» создана.", reply_markup=markup)
                await state.clear()
    except Exception as ex:
        logging.info(f"Ошибка {ex}")
        await msg.answer("Ошибка в базе данных")


@category_router.message(Command("remove_category"))
async def cmd_remove_cat(msg: Message):
    try:
        with get_db() as db:
            cats = db.query(Category).order_by(Category.name).all()
            if not cats:
                await msg.answer("Категории отсутствуют.")
                return
            builder = InlineKeyboardBuilder()
            for category in cats:
                builder.button(
                    text=category.name,
                    callback_data=f"del_cat_{category.id}"
                )
            builder.adjust(2)
            await msg.answer(
                "Выберите категорию события:",
                reply_markup=builder.as_markup()
            )
    except Exception as e:
        logging.info(f"Ошибка в remove_category {e}")
        await msg.answer("Ошибка в базе данных")


@category_router.callback_query(F.data.startswith("del_cat_"))
async def process_del_cat(call: CallbackQuery):
    cat_id = int(call.data.split("_")[-1])
    with get_db() as db:
        cat = db.query(Category).get(cat_id)
        if not cat:
            await call.message.answer("Категория не найдена.")
        else:
            db.delete(cat)
            # db.commit() is automatic
            await call.message.answer(f"Категория «{cat.name}» удалена.")


@category_router.callback_query(F.data == "manage_category")
async def manage_categories_handler(callback: CallbackQuery):
    with get_db() as db:
        categories = db.query(Category).order_by(Category.name).all()

    if not categories:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="➕ Добавить категорию",
            callback_data="add_category"
        )
        builder.button(
            text="◀️Назад",
            callback_data="admin_panel"
        )
        builder.adjust(1)
        await callback.message.answer("Список категорий пуст.", reply_markup=builder.as_markup())
        return
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=f"🗑️ Удалить «{category.name}»",
            callback_data=f"del_cat_{category.id}"
        )
    builder.button(
        text="➕ Добавить категорию",
        callback_data="add_category"
    )
    builder.button(
        text="◀️Назад",
        callback_data="admin_panel"
    )
    builder.adjust(1)
    await callback.message.answer(
        "📂 Список категорий:",
        reply_markup=builder.as_markup()
    )