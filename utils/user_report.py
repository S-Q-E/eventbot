import pandas as pd
from db.database import get_db, User
import datetime


def generate_user_report():
    db = next(get_db())
    try:
        # Получение всех пользователей из БД
        users = db.query(User).all()

        # Подготовка данных для DataFrame
        data = []
        for user in users:
            data.append({
                "ID": user.id,
                "Имя": user.first_name,
                "Фамилия": user.last_name,
                "Username": user.username or "Нет",
                "Статус регистрации": "Зарегистрирован" if user.is_registered else "Не зарегистрирован",
                "Номер телефона": user.phone_number
            })

        # Создание DataFrame и запись в Excel
        df = pd.DataFrame(data)
        filename = f"user_report_{datetime.date.today()}.xlsx"
        df.to_excel(filename, index=False)

        return filename  # Возвращаем путь к файлу
    finally:
        db.close()
