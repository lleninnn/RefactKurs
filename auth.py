# auth.py
# Модуль отвечает за регистрацию и вход пользователей.
# Использует bcrypt для безопасного хеширования паролей.

import bcrypt
from database import save_user, get_user

def register(username, password):
    """
    Регистрирует нового пользователя.
    :param username: имя пользователя (минимум 3 символа)
    :param password: пароль (минимум 6 символов)
    :return: кортеж (успех, сообщение)
    """
    if len(username) < 3 or len(password) < 6:
        return False, 'Имя пользователя должно быть не менее 3 символов, а пароль - не менее 6.'

    # Проверяем, не занято ли имя
    user = get_user(username)
    if user:
        return False, 'Пользователь уже существует.'

    # Хешируем пароль
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    success, msg = save_user(username, hashed)
    return success, msg

def login(username, password):
    """
    Выполняет вход пользователя.
    :param username: имя пользователя
    :param password: пароль
    :return: кортеж (успех, сообщение, имя пользователя)
    """
    user = get_user(username)
    if not user:
        return False, 'Пользователь не найден.', None

    stored_hash = user[1].encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return True, 'Вход успешен.', username
    else:
        return False, 'Неверный пароль.', None