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
    db = next(get_db())
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="К категориям", callback_data="manage_category")
    keyboard.adjust(1)
    markup = keyboard.as_markup()
    try:
        if db.query(Category).filter_by(name=name).first():
            await msg.answer("Категория с таким именем уже есть.")
        else:
            db.add(Category(name=name))
            db.commit()
            await msg.answer(f"Категория «{name}» создана.", reply_markup=markup)
            await state.clear()
    except Exception as ex:
        logging.info(f"Ошибка {ex}")
        await msg.answer("Ошибка в базе данных")
    finally:
        db.close()


@category_router.message(Command("remove_category"))
async def cmd_remove_cat(msg: Message):
    db = next(get_db())
    try:
        cats = db.query(Category).order_by(Category.name).all()
        if not cats:
            await msg.answer("Категории отсутствуют.")
            db.close()
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
    finally:
        db.close()


@category_router.callback_query(F.data.startswith("del_cat_"))
async def process_del_cat(call: CallbackQuery):
    cat_id = int(call.data.split("_")[-1])
    db = next(get_db())

    cat = db.query(Category).get(cat_id)
    if not cat:
        await call.message.answer("Категория не найдена.")
    else:
        db.delete(cat)
        db.commit()
        await call.message.answer(f"Категория «{cat.name}» удалена.")
    db.close()


@category_router.callback_query(F.data == "manage_category")
async def manage_categories_handler(callback: CallbackQuery):
    db = next(get_db())
    categories = db.query(Category).order_by(Category.name).all()
    db.close()

    if not categories:
        await callback.message.answer("Список категорий пуст.")
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
    builder.adjust(1)
    await callback.message.answer(
        "📂 Список категорий:",
        reply_markup=builder.as_markup()
    )