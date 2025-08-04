#!/usr/bin/env python3
"""
Тест логики сопоставления ID кандидатов
"""

def test_id_extraction():
    """Тестирует извлечение ID из текста опции"""
    
    # Тестовые данные
    test_options = [
        "Иван Иванов (ID:123)",
        "Петр Петров (ID:456)",
        "Сидор Сидоров (ID:789)",
        "Анна Петрова (ID:101)"
    ]
    
    print("🧪 Тестирование извлечения ID из опций опроса...")
    
    for i, option_text in enumerate(test_options):
        try:
            # Логика извлечения ID (как в handle_poll)
            if "(ID:" in option_text:
                id_start = option_text.find("(ID:") + 4
                id_end = option_text.find(")", id_start)
                candidate_id = int(option_text[id_start:id_end])
                
                # Извлекаем имя
                name_end = option_text.find(" (ID:")
                name = option_text[:name_end] if name_end != -1 else option_text
                
                print(f"  ✅ Опция {i}: '{name}' -> ID: {candidate_id}")
            else:
                print(f"  ❌ Опция {i}: '{option_text}' - не содержит ID")
                
        except (ValueError, IndexError) as e:
            print(f"  ❌ Ошибка при обработке '{option_text}': {e}")
    
    print("✅ Тест извлечения ID завершен!")

def test_candidate_matching():
    """Тестирует сопоставление кандидатов по ID"""
    
    # Симуляция кандидатов из базы данных
    candidates = [
        {"id": 123, "name": "Иван Иванов", "votes": 0},
        {"id": 456, "name": "Петр Петров", "votes": 0},
        {"id": 789, "name": "Сидор Сидоров", "votes": 0}
    ]
    
    # Симуляция результатов опроса
    poll_results = [
        {"text": "Иван Иванов (ID:123)", "votes": 5},
        {"text": "Петр Петров (ID:456)", "votes": 3},
        {"text": "Сидор Сидоров (ID:789)", "votes": 7}
    ]
    
    print("\n🧪 Тестирование сопоставления кандидатов...")
    
    for poll_option in poll_results:
        try:
            if "(ID:" in poll_option["text"]:
                id_start = poll_option["text"].find("(ID:") + 4
                id_end = poll_option["text"].find(")", id_start)
                candidate_id = int(poll_option["text"][id_start:id_end])
                
                # Находим кандидата по ID
                candidate = next((c for c in candidates if c["id"] == candidate_id), None)
                if candidate:
                    old_votes = candidate["votes"]
                    candidate["votes"] = poll_option["votes"]
                    print(f"  ✅ Обновлен {candidate['name']}: {old_votes} -> {candidate['votes']} голосов")
                else:
                    print(f"  ❌ Кандидат с ID {candidate_id} не найден")
                    
        except (ValueError, IndexError) as e:
            print(f"  ❌ Ошибка при обработке '{poll_option['text']}': {e}")
    
    # Определяем победителя
    winner = max(candidates, key=lambda c: c["votes"])
    print(f"\n🏆 Победитель: {winner['name']} с {winner['votes']} голосами")
    
    print("✅ Тест сопоставления завершен!")

if __name__ == "__main__":
    test_id_extraction()
    test_candidate_matching() 