import pandas as pd
import sqlite3
import re
import sys

DB_PATH = 'events.db'
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else 'users.xlsx'

def parse_user_row(row: str):
    """
    Пример строки: "3 Иван Иванов ID: 1234567890" или "Иван Иванов ID: 1234567890"
    """
    match = re.search(r'(?:(\d+)\s+)?(.+?)\s+ID:\s*(\d+)', row)
    if not match:
        return None
    games = int(match.group(1)) if match.group(1) else 1
    user_id = int(match.group(3))
    return games, user_id

def read_input_file(path):
    if path.endswith('.csv'):
        df = pd.read_csv(path, header=None)
    elif path.endswith('.xlsx') or path.endswith('.xls'):
        df = pd.read_excel(path, header=None)
    else:
        raise ValueError("Поддерживаются только .csv и .xlsx файлы")
    return df[0].astype(str).tolist()

def update_database(entries):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated = 0
    for games, user_id in entries:
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if cursor.fetchone():
            cursor.execute('UPDATE users SET user_games = ? WHERE id = ?', (games, user_id))
            print(f'✔ Обновлён ID {user_id} — игр: {games}')
            updated += 1
        else:
            print(f'✘ ID {user_id} не найден в БД, пропущен')

    conn.commit()
    conn.close()
    print(f'✅ Всего обновлено: {updated} записей')

def main():
    print(f'📄 Чтение файла: {INPUT_FILE}')
    rows = read_input_file(INPUT_FILE)
    entries = []

    for row in rows:
        parsed = parse_user_row(row)
        if parsed:
            entries.append(parsed)
        else:
            print(f'⚠ Пропущено (не распознано): {row}')

    update_database(entries)

if __name__ == '__main__':
    main()
