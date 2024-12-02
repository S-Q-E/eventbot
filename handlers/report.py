from aiogram import types, Router, F
from aiogram.types import FSInputFile

from utils.user_report import generate_user_report

report_router = Router()


@report_router.callback_query(F.data == "report")
async def send_report(callback: types.CallbackQuery):
    file_name = generate_user_report()
    report = FSInputFile(file_name)
    await callback.message.answer("Ваш отчет сгенерирован!")
    await callback.message.answer_document(report)




