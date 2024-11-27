import logging
import pytesseract
from PIL import Image
import re
import io
import asyncio


def clean_name(name):
    """Удаляет лишние символы и пробелы, оставляя только буквы и пробелы."""
    return re.sub(r'[^\w\s]', '', name).strip().lower()


async def parse_receipt(image_data: bytes, expected_amount: float, expected_name: str) -> bool:
    try:
        image = Image.open(io.BytesIO(image_data))
        text = await asyncio.to_thread(pytesseract.image_to_string, image, lang='rus')
        logging.info(f"Извлеченный текст:\n{text}")

        # Проверка суммы перевода
        amount_match = re.search(r'Сумма(?:\s*перевода)?\s*([\d\s.,]+)', text)
        if not amount_match:
            logging.error("Сумма не найдена.")
            return False

        amount = float(amount_match.group(1).replace(" ", "").replace(",", "."))
        logging.info(f"Извлеченная сумма: {amount}")

        if amount != expected_amount:
            logging.error(f"Несоответствие суммы. Ожидаемая: {expected_amount}, Найденная: {amount}")
            return False

        # Проверка имени получателя с учётом сокращений
        name_match = re.search(r'ФИО получателя\s*(.*)', text, re.IGNORECASE)
        if not name_match:
            logging.error("ФИО получателя не найдено.")
            return False

        receipt_name = clean_name(name_match.group(1))
        expected_name = clean_name(expected_name)
        logging.info(f"Извлеченное ФИО: {receipt_name}")

        # Сравнение только имени и фамилии (без отчества)
        if not all(part in receipt_name for part in expected_name.split()[:2]):
            logging.error(f"Несоответствие ФИО. Ожидаемое: {expected_name}, Найденное: {receipt_name}")
            return False

        return True

    except Exception as e:
        logging.error(f"Ошибка при обработке чека: {e}")
        return False