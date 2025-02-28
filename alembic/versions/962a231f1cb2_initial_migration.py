from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250206_01'
down_revision = None  # или укажите предыдущий revision, если он есть
branch_labels = None
depends_on = None

def upgrade():
    # Пример миграции для таблицы "users" с использованием batch mode
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Например, изменяем тип столбца username (увеличиваем длину до 100 символов)
        batch_op.alter_column('username',
                              existing_type=sa.String(),
                              type_=sa.String(100),
                              existing_nullable=True)
        # Если необходимо удалить какое-либо ограничение, можно использовать:
        # batch_op.drop_constraint('some_constraint_name', type_='unique')

    # Пример миграции для таблицы "events"
    # Создание индекса на столбец event_time с проверкой существования
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_events_event_time ON events (event_time)"
    )

def downgrade():
    # Откат миграции для таблицы "events" — удаление индекса (если он существует)
    op.execute(
        "DROP INDEX IF EXISTS ix_events_event_time"
    )

    # Откат изменений в таблице "users"
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username',
                              existing_type=sa.String(100),
                              type_=sa.String(),
                              existing_nullable=True)
        # Если ранее удаляли ограничение, его можно восстановить, например:
        # batch_op.create_unique_constraint('some_constraint_name', ['username'])
