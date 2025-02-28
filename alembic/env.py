import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Добавляем родительскую директорию в sys.path, чтобы Alembic смог импортировать ваши модели.
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import Base  # Импорт Base с вашими моделями

# Получаем конфигурацию Alembic из файла alembic.ini.
config = context.config

# Настройка логирования из файла конфигурации.
fileConfig(config.config_file_name)

# Указываем целевые метаданные (они используются для autogenerate миграций)
target_metadata = Base.metadata

def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True  # Для SQLite обязательно использовать batch mode
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Запуск миграций в онлайн-режиме."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool  # для SQLite обычно NullPool подходит
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # отслеживание изменений типов столбцов
            render_as_batch=True  # включаем batch mode для SQLite
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
