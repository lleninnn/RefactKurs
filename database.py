# database.py
# Модуль обеспечивает взаимодействие с SQLite базой данных.
# Использует контекстный менеджер для автоматического закрытия соединений.

import sqlite3
from datetime import datetime
import json
from contextlib import contextmanager

DATABASE_FILE = 'chess.db'

@contextmanager
def get_connection():
    """
    Контекстный менеджер для получения соединения с БД.
    Гарантирует закрытие соединения после выхода из блока.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        yield conn
    finally:
        conn.close()

def initialize_db():
    """Создаёт таблицы users и games, если они ещё не существуют."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                white_player TEXT NOT NULL,
                black_player TEXT NOT NULL,
                moves TEXT NOT NULL,
                result TEXT,
                start_time TEXT,
                end_time TEXT,
                status TEXT NOT NULL
            )
        ''')
        conn.commit()

# ---------- Пользователи ----------
def save_user(username, password_hash):
    """Сохраняет нового пользователя в таблицу users."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                           (username, password_hash))
            conn.commit()
            return True, 'Пользователь успешно зарегистрирован.'
        except sqlite3.IntegrityError:
            return False, 'Пользователь уже существует.'

def get_user(username):
    """Возвращает запись пользователя по имени или None, если не найден."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()

# ---------- Игры ----------
def create_new_game(white_player, black_player):
    """Создаёт новую запись о партии и возвращает её ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        moves_json = json.dumps([])   # пустой список ходов
        cursor.execute('''
            INSERT INTO games (white_player, black_player, moves, result, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (white_player, black_player, moves_json, None, start_time, None, 'in_progress'))
        game_id = cursor.lastrowid
        conn.commit()
        return game_id

def update_game(game_id, moves, result=None, end_time=None, status='in_progress'):
    """Обновляет данные существующей партии."""
    with get_connection() as conn:
        cursor = conn.cursor()
        moves_json = json.dumps(moves)
        cursor.execute('''
            UPDATE games
            SET moves = ?, result = ?, end_time = ?, status = ?
            WHERE game_id = ?
        ''', (moves_json, result, end_time, status, game_id))
        conn.commit()

def get_games_by_user(username, status=None):
    """
    Возвращает список партий, в которых участвует пользователь.
    Если указан status, фильтрует по статусу.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute('''
                SELECT * FROM games 
                WHERE (white_player = ? OR black_player = ?) AND status = ?
                ORDER BY start_time DESC
            ''', (username, username, status))
        else:
            cursor.execute('''
                SELECT * FROM games 
                WHERE white_player = ? OR black_player = ?
                ORDER BY start_time DESC
            ''', (username, username))
        return cursor.fetchall()

def get_game_by_id(game_id):
    """Возвращает данные партии по её ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM games WHERE game_id = ?', (game_id,))
        return cursor.fetchone()