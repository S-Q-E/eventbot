import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery
from db.database import User
from middlewares.registration_middleware import RegistrationMiddleware


@pytest.fixture
def middleware():
    return RegistrationMiddleware()

@pytest.fixture
def mock_db_session():
    # Создаем фиктивную сессию базы данных
    with patch("db.database.get_db") as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value = iter([mock_session])
        yield mock_session

@pytest.fixture
def mock_event():
    # Создаем фиктивное сообщение с user_id
    event = MagicMock()
    event.from_user = MagicMock(id=123)
    event.answer = AsyncMock()
    return event

@pytest.fixture
def mock_handler():
    # Создаем фиктивный обработчик
    return AsyncMock()

async def test_user_not_in_database(middleware, mock_event, mock_handler, mock_db_session):
    # Тест, когда пользователя нет в базе данных
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    await middleware(mock_handler, mock_event, {})

    # Проверяем, что пользователь был добавлен
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

    # Проверяем, что сообщение о необходимости регистрации было отправлено
    mock_event.answer.assert_awaited_once_with("Вы не зарегистрированы", reply_markup=Any)

async def test_user_not_registered(middleware, mock_event, mock_handler, mock_db_session):
    # Тест, когда пользователь есть в базе, но не зарегистрирован
    user = User(id=123, is_registered=False)
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = user

    await middleware(mock_handler, mock_event, {})

    # Проверяем, что сообщение о необходимости регистрации было отправлено
    mock_event.answer.assert_awaited_once_with("Вы не зарегистрированы. Пожалуйста, пройдите регистрацию.", reply_markup=Any)

async def test_user_registered(middleware, mock_event, mock_handler, mock_db_session):
    # Тест, когда пользователь зарегистрирован
    user = User(id=123, is_registered=True)
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = user

    await middleware(mock_handler, mock_event, {})

    # Проверяем, что сообщение о регистрации НЕ было отправлено
    mock_event.answer.assert_not_called()
    # Проверяем, что управление передано основному хендлеру
    mock_handler.assert_awaited_once_with(mock_event, {})
