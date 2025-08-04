#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений в системе голосования
"""

import logging
from datetime import datetime
from db.database import get_db, User, Event, Registration
from utils.mvp_poll import choose_mvp_candidate, announce_winner

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_voting_system():
    """
    Тестирует основные функции системы голосования
    """
    print("🧪 Тестирование системы голосования...")
    
    db = next(get_db())
    try:
        # Проверяем текущих кандидатов
        candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        print(f"📊 Текущих кандидатов: {len(candidates)}")
        
        for candidate in candidates:
            print(f"  - {candidate.first_name} {candidate.last_name} (ID: {candidate.id}): {candidate.votes} голосов")
        
        # Проверяем завершенные события
        now = datetime.now()
        events = db.query(Event).filter(
            Event.event_time < now,
            Event.is_checked == False,
            Event.category_id == 2
        ).all()
        
        print(f"📅 Найдено {len(events)} завершенных событий для обработки")
        
        # Тестируем выбор кандидатов
        for event in events:
            print(f"🎯 Обрабатываем событие: {event.name} (ID: {event.id})")
            candidate = choose_mvp_candidate(event.id)
            if candidate:
                print(f"  ✅ Выбран кандидат: {candidate.first_name} {candidate.last_name} (ID: {candidate.id})")
            else:
                print(f"  ❌ Кандидат не найден для события {event.id}")
        
        # Проверяем результат
        updated_candidates = db.query(User).filter(User.is_mvp_candidate == True).all()
        print(f"📊 Кандидатов после обработки: {len(updated_candidates)}")
        
        for candidate in updated_candidates:
            print(f"  - {candidate.first_name} {candidate.last_name} (ID: {candidate.id}): {candidate.votes} голосов")
        
        print("✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_voting_system() 