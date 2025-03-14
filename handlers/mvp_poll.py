import os
from aiogram import Router, types, F
from utils.send_pool import send_mvp_poll, process_mvp_results
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

GROUP_CHAT_ID = os.getenv("CHAT_ID")

mvp_router = Router()


@mvp_router.callback_query(F.data.startswith("select_mvp"))
async def start_mvp(callback: types.CallbackQuery):
    event_id = int(callback.message.text.split("_")[-1])
    await send_mvp_poll(callback.message.bot, event_id)


@mvp_router.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer):
    """Обрабатывает результаты голосования."""
    event_id = 1  # Здесь нужно получить ID события
    results = poll_answer.option_ids
    await process_mvp_results(poll_answer.bot, event_id, results)
