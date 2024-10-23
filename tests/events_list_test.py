import unittest
from unittest.mock import MagicMock, patch
from aiogram.types import CallbackQuery, Message

from db.database import Event
from handlers.events_list import list_events


class TestEventListHandler(unittest.TestCase):

    @patch("handlers.event_list.get_db")
    @patch("handlers.event_list.CallbackQuery")
    async def test_list_events_with_events(self, mock_callback_query, mock_get_db):
        # Создаем моки событий
        event_1 = Event(id=1, name="Концерт", event_time="2024-10-23 18:00", description="Концерт в парке", price=100,
                        max_participants=50, current_participants=10)
        event_2 = Event(id=2, name="Лекция", event_time="2024-10-24 14:00", description="Лекция по истории", price=0,
                        max_participants=30, current_participants=5)

        # Мок базы данных
        mock_get_db.return_value.query.return_value.all.return_value = [event_1, event_2]

        # Мок CallbackQuery
        mock_callback_query.message.edit_reply_markup = MagicMock()
        mock_callback_query.message.answer = MagicMock()

        # Вызываем хэндлер
        await list_events(mock_callback_query)

        # Проверяем, что ответ был отправлен дважды для двух событий
        self.assertEqual(mock_callback_query.message.answer.call_count, 2)

        # Проверка содержимого ответа для первого события
        expected_message_1 = (
            "🎉 <b>Концерт</b>\n"
            "🕒 <b>Дата:</b> 23 October\n\n"
            "📝 <b>Описание:</b> Концерт в парке\n"
            "💰 <b>Цена</b>: 100\n"
            "💡 <b>Осталось мест</b>: 40"
        )
        mock_callback_query.message.answer.assert_any_call(expected_message_1, reply_markup=MagicMock(),
                                                           parse_mode="HTML")

    @patch("handlers.event_list.get_db")
    @patch("handlers.event_list.CallbackQuery")
    async def test_list_events_no_events(self, mock_callback_query, mock_get_db):
        # Мок базы данных без событий
        mock_get_db.return_value.query.return_value.all.return_value = []

        # Мок CallbackQuery
        mock_callback_query.message.edit_reply_markup = MagicMock()
        mock_callback_query.message.answer = MagicMock()

        # Вызываем хэндлер
        await list_events(mock_callback_query)

        # Проверяем, что сообщение о пустом списке отправлено
        mock_callback_query.message.answer.assert_called_with("Нет доступных событий.")


if __name__ == '__main__':
    unittest.main()
