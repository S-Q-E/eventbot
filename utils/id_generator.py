import uuid
from db.database import User, get_db


def generate_unique_id_with_uuid(db) -> int:
    """
    Генерирует уникальный 10-значный ID с использованием UUID, проверяет его в базе данных.

    :param db: Экземпляр сессии SQLAlchemy.
    :return: Уникальный 10-значный ID.
    """
    while True:
        # Генерация UUID и преобразование его в 10-значный ID
        new_id = int(str(uuid.uuid4().int)[:10])

        # Проверка уникальности ID в базе данных
        if not db.query(User).filter(User.id == new_id).first():
            return new_id
