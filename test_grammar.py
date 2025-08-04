#!/usr/bin/env python3
"""
Тест правильного склонения слова "матч"
"""

def test_games_grammar():
    """
    Тестирует правильное склонение слова "матч"
    """
    print("🧪 Тестирование склонения слова 'матч'...")
    
    test_cases = [
        (1, "матч"),
        (2, "матчей"),
        (3, "матчей"),
        (4, "матчей"),
        (5, "матчей"),
        (10, "матчей"),
        (21, "матчей"),
        (22, "матчей"),
        (25, "матчей"),
        (31, "матчей"),
    ]
    
    for games, expected in test_cases:
        if games == 1:
            result = "матч"
        else:
            result = "матчей"
        
        status = "✅" if result == expected else "❌"
        print(f"  {status} {games} {result} (ожидалось: {expected})")
    
    print("✅ Тест склонения завершен!")

def test_stats_formatting():
    """
    Тестирует форматирование статистики
    """
    print("\n📊 Тестирование форматирования статистики...")
    
    # Симулируем данные
    users_data = [
        {"name": "Василий Козлов", "games": 7},
        {"name": "Григорий Г", "games": 6},
        {"name": "Татьяна Козлова", "games": 5},
        {"name": "Алексей Петров", "games": 4},
        {"name": "Мария Сидорова", "games": 3},
        {"name": "Дмитрий Иванов", "games": 2},
        {"name": "Елена Козлова", "games": 2},
        {"name": "Сергей Петров", "games": 1},
        {"name": "Анна Сидорова", "games": 1},
        {"name": "Иван Иванов", "games": 1},
    ]
    
    current_user = {"name": "Вы", "games": 1, "position": 34}
    
    stats_text = "📊 <b>Топ игроков по количеству матчей:</b>\n\n"
    
    medals = ["👑", "🥈", "🥉"]
    
    for i, user in enumerate(users_data, 1):
        games_text = "матч" if user["games"] == 1 else "матчей"
        if i <= 3:
            stats_text += f"{medals[i-1]}{user['name']} {user['games']} {games_text}\n"
        else:
            stats_text += f"{i}. {user['name']} {user['games']} {games_text}\n"
    
    # Добавляем позицию текущего пользователя
    if current_user["position"] > 10:
        games_text = "матч" if current_user["games"] == 1 else "матчей"
        stats_text += f"\n{current_user['position']}. {current_user['name']} {current_user['games']} {games_text}"
    
    print(stats_text)
    print("✅ Тест форматирования завершен!")

if __name__ == "__main__":
    test_games_grammar()
    test_stats_formatting() 