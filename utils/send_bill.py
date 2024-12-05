from yookassa import Receipt


async def create_and_send_receipt(payment, admin_chat_id, bot):
    try:
        payment_method = payment.payment_method.type  # Получаем способ оплаты
        user_email = "user@example.com"  # Замените на реальный email пользователя из вашей БД

        # Создание чека с учётом метода оплаты
        receipt = Receipt.create({
            "customer": {
                "email": user_email  # Используйте email из БД или Telegram-аккаунта
            },
            "payment_id": payment.id,
            "type": "payment",
            "send": False,  # Автоматическая отправка чека на email пользователя
            "items": [
                {
                    "description": f"Участие в событии",
                    "quantity": 1.0,
                    "amount": {
                        "value": payment.amount.value,  # Сумма из объекта платежа
                        "currency": payment.amount.currency
                    },
                    "vat_code": 1  # Убедитесь, что этот код НДС корректен для вас
                }
            ]
        })

        # Формирование сообщения для администратора
        receipt_info = (
            f"📄 Чек об оплате:\n"
            f"🆔 ID чека: {receipt.id}\n"
            f"💰 Сумма: {receipt.amount['value']} {receipt.amount['currency']}\n"
            f"🛠 Способ оплаты: {payment_method}\n"
            f"👤 Email плательщика: {user_email}\n"
            f"🕒 Дата создания: {receipt.created_at}\n"
        )

        # Отправка сообщения администратору
        await bot.send_message(admin_chat_id, receipt_info)
    except Exception as e:
        await bot.send_message(admin_chat_id, f"❌ Ошибка при создании чека: {e}")