#!/usr/bin/env python3
"""
Тестовый скрипт для проверки статистики пользователей
"""

import logging
from db.database import get_db, User

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_user_statistics():
    """
    Тестирует функцию статистики пользователей
    """
    print("🧪 Тестирование статистики пользователей...")
    
    db = next(get_db())
    try:
        # Получаем всех пользователей с играми, отсортированных по убыванию
        users = db.query(User).filter(User.user_games > 0).order_by(User.user_games.desc()).all()
        
        print(f"📊 Найдено {len(users)} пользователей с играми")
        
        if not users:
            print("❌ Нет пользователей с играми")
            return
        
        # Берем первого пользователя как текущего для теста
        current_user = users[0]
        current_user_id = current_user.id
        
        print(f"\n👤 Текущий пользователь: {current_user.first_name} {current_user.last_name} (ID: {current_user.id})")
        print(f"🎮 Игр у текущего пользователя: {current_user.user_games}")
        
        # Формируем топ-10
        print("\n📊 Топ игроков по количеству матчей:")
        medals = ["👑", "🥈", "🥉"]
        
        for i, user in enumerate(users[:10], 1):
            if i <= 3:
                print(f"  {medals[i-1]}{user.first_name} {user.last_name} {user.user_games} матчей")
            else:
                print(f"  {i}. {user.first_name} {user.last_name} {user.user_games} матчей")
        
        # Проверяем позицию текущего пользователя
        current_user_position = None
        for i, user in enumerate(users, 1):
            if user.id == current_user_id:
                current_user_position = i
                break
        
        print(f"\n📍 Позиция текущего пользователя: {current_user_position}")
        
        # Если пользователь не в топ-10, показываем его позицию
        if current_user_position and current_user_position > 10:
            current_user_games = current_user.user_games
            games_text = "матчей" if current_user_games != 1 else "матч"
            print(f"  {current_user_position}. Вы {current_user_games} {games_text}")
        
        print("\n✅ Тест статистики завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        db.close()

def simulate_stats_output():
    """
    Симулирует вывод статистики как в боте
    """
    print("\n📱 Симуляция вывода в боте:")
    print("=" * 50)
    
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
        if i <= 3:
            stats_text += f"{medals[i-1]}{user['name']} {user['games']} матчей\n"
        else:
            stats_text += f"{i}. {user['name']} {user['games']} матчей\n"
    
    # Добавляем позицию текущего пользователя
    if current_user["position"] > 10:
        games_text = "матч" if current_user["games"] == 1 else "матчей"
        stats_text += f"\n{current_user['position']}. {current_user['name']} {current_user['games']} {games_text}"
    
    print(stats_text)
    print("=" * 50)

if __name__ == "__main__":
    test_user_statistics()
    simulate_stats_output() 