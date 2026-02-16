# main.py
# Основной исполняемый файл. Запускает игру, управляет экранами
# (аутентификация, выбор режима, просмотр партий, игровой процесс).

import pygame
import sys
import os
import json
import settings
from auth import login, register
from database import initialize_db, get_games_by_user, create_new_game, get_game_by_id
from game import Game, Move
from ai import find_best_move
from renderer import GameRenderer

pygame.init()
pygame.display.set_caption('Шахматный Эндшпиль: Король и Пешка - Король и Пешка')

# Настройка окна в зависимости от режима FULLSCREEN
if settings.FULLSCREEN:
    info = pygame.display.Info()
    settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.FULLSCREEN)
    # Масштабируем размер клетки под экран
    settings.CELL_SIZE = min(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT) // settings.BOARD_SIZE
else:
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))

clock = pygame.time.Clock()

def load_images():
    """
    Загружает все изображения из папки assets.
    Возвращает словарь, где ключ – код фигуры (например 'wK'), значение – Surface.
    """
    images = {}
    filename_to_key = {
        'king_white.png': 'wK',
        'king_black.png': 'bK',
        'queen_white.png': 'wQ',
        'queen_black.png': 'bQ',
        'pawn_white.png': 'wP',
        'pawn_black.png': 'bP',
        'bishop_white.png': 'wB',
        'bishop_black.png': 'bB',
        'horse_white.png': 'wN',
        'horse_black.png': 'bN',
        'tower_white.png': 'wR',
        'tower_black.png': 'bR',
        'eye_open.png': 'eye_open',
        'eye_closed.png': 'eye_closed'
    }
    for filename in os.listdir(settings.ASSETS_PATH):
        if filename.endswith('.png'):
            path = os.path.join(settings.ASSETS_PATH, filename)
            key = filename_to_key.get(filename)
            if key:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Масштабируем иконки глаз отдельно
                    if filename in ['eye_open.png', 'eye_closed.png']:
                        eye_size = 30
                        img = pygame.transform.scale(img, (eye_size, eye_size))
                    else:
                        img = pygame.transform.scale(img, (settings.CELL_SIZE, settings.CELL_SIZE))
                    images[key] = img
                    print(f"Загружено изображение: {filename}")
                except pygame.error as e:
                    print(f"Ошибка загрузки изображения {path}: {e}")
            else:
                print(f"Неизвестное изображение: {filename}")
    # Проверка наличия всех необходимых ключей
    required_keys = ['wK', 'bK', 'wP', 'bP', 'wQ', 'bQ', 'wR', 'bR', 'wB', 'bB', 'wN', 'bN', 'eye_open', 'eye_closed']
    for key in required_keys:
        if key not in images:
            print(f"Предупреждение: Изображение для {key} не найдено.")
    return images

images = load_images()
renderer = GameRenderer(screen, images)

# ---------- Вспомогательные функции для отрисовки текста ----------
def draw_text(win, text, size, color, x, y):
    """Отрисовывает текст заданным шрифтом и размером."""
    font = pygame.font.SysFont('Arial', size)
    text_surface = font.render(text, True, color)
    win.blit(text_surface, (x, y))

# ---------- Экраны аутентификации ----------
def auth_screen():
    """Главное меню: вход, регистрация, выход."""
    message = ''
    while True:
        screen.fill(settings.BLACK)
        draw_text(screen, 'Шахматный Эндшпиль', 60, settings.WHITE, settings.WINDOW_WIDTH // 2 - 200, 50)
        draw_text(screen, '1. Войти', 40, settings.WHITE, 100, 200)
        draw_text(screen, '2. Зарегистрироваться', 40, settings.WHITE, 100, 300)
        draw_text(screen, '3. Выход', 40, settings.WHITE, 100, 400)
        draw_text(screen, 'Нажмите TAB для переключения между опциями', 20, settings.WHITE, 100, 500)
        draw_text(screen, message, 30, settings.RED, 100, 600)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    success, msg, user = login_prompt()
                    if success:
                        return user
                    else:
                        message = msg
                if event.key == pygame.K_2:
                    success, msg = register_prompt()
                    message = msg
                if event.key == pygame.K_3:
                    pygame.quit()
                    sys.exit()
        clock.tick(settings.FPS)

def login_prompt():
    """
    Экран входа. Позволяет ввести имя и пароль, переключать видимость пароля.
    Возвращает (успех, сообщение, имя пользователя).
    """
    username = ''
    password = ''
    input_box = 'username'   # какое поле активно
    message = ''
    password_visible = False
    eye_icon = images.get('eye_closed')
    # Позиция иконки глаза привязана к полю пароля
    eye_rect = pygame.Rect(500 + 200 + 10, 300 + (50 - 30) // 2, 30, 30)

    while True:
        screen.fill(settings.BLACK)
        draw_text(screen, 'Вход', 50, settings.WHITE, settings.WINDOW_WIDTH // 2 - 80, 50)
        draw_text(screen, 'Имя пользователя:', 35, settings.WHITE, 100, 200)
        draw_text(screen, username, 35, settings.WHITE, 500, 200)
        draw_text(screen, 'Пароль:', 35, settings.WHITE, 100, 300)
        if password_visible:
            display_password = password
        else:
            display_password = '*' * len(password)
        draw_text(screen, display_password, 35, settings.WHITE, 500, 300)
        draw_text(screen, 'Нажмите TAB для переключения между полями ввода', 25, settings.WHITE, 100, 400)
        draw_text(screen, 'Нажмите ESC для возврата в главное меню', 25, settings.WHITE, 100, 450)
        draw_text(screen, message, 30, settings.RED, 100, 500)

        # Подсветка активного поля
        if input_box == 'username':
            pygame.draw.rect(screen, settings.BLUE, pygame.Rect(500, 200, 200, 50), 3)
        else:
            pygame.draw.rect(screen, settings.BLUE, pygame.Rect(500, 300, 200, 50), 3)

        # Рисуем иконку глаза
        if password_visible:
            eye_icon = images.get('eye_open')
        else:
            eye_icon = images.get('eye_closed')
        if eye_icon:
            screen.blit(eye_icon, eye_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if eye_rect.collidepoint(event.pos):
                    password_visible = not password_visible
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_box = 'password' if input_box == 'username' else 'username'
                elif event.key == pygame.K_ESCAPE:
                    return False, 'Возврат в главное меню.', None
                elif event.key == pygame.K_RETURN:
                    if len(username) < 3 or len(password) < 6:
                        message = 'Имя пользователя ≥ 3 символа, пароль ≥ 6 символов.'
                    else:
                        success, msg, user = login(username, password)
                        if success:
                            return True, msg, user
                        else:
                            message = msg
                elif event.key == pygame.K_BACKSPACE:
                    if input_box == 'username':
                        username = username[:-1]
                    else:
                        password = password[:-1]
                else:
                    if input_box == 'username' and event.unicode.isprintable():
                        username += event.unicode
                    elif input_box == 'password' and event.unicode.isprintable():
                        password += event.unicode
        clock.tick(settings.FPS)

def register_prompt():
    """
    Экран регистрации нового пользователя.
    Возвращает (успех, сообщение).
    """
    username = ''
    password = ''
    input_box = 'username'
    message = ''
    password_visible = False
    eye_icon = images.get('eye_closed')
    eye_rect = pygame.Rect(500 + 200 + 10, 300 + (50 - 30) // 2, 30, 30)

    while True:
        screen.fill(settings.BLACK)
        draw_text(screen, 'Регистрация', 50, settings.WHITE, settings.WINDOW_WIDTH // 2 - 120, 50)
        draw_text(screen, 'Имя пользователя:', 35, settings.WHITE, 100, 200)
        draw_text(screen, username, 35, settings.WHITE, 500, 200)
        draw_text(screen, 'Пароль:', 35, settings.WHITE, 100, 300)
        if password_visible:
            display_password = password
        else:
            display_password = '*' * len(password)
        draw_text(screen, display_password, 35, settings.WHITE, 500, 300)
        draw_text(screen, 'Нажмите TAB для переключения между полями ввода', 25, settings.WHITE, 100, 400)
        draw_text(screen, 'Нажмите ESC для возврата в главное меню', 25, settings.WHITE, 100, 450)
        draw_text(screen, message, 30, settings.RED, 100, 500)

        if input_box == 'username':
            pygame.draw.rect(screen, settings.BLUE, pygame.Rect(500, 200, 200, 50), 3)
        else:
            pygame.draw.rect(screen, settings.BLUE, pygame.Rect(500, 300, 200, 50), 3)

        if password_visible:
            eye_icon = images.get('eye_open')
        else:
            eye_icon = images.get('eye_closed')
        if eye_icon:
            screen.blit(eye_icon, eye_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if eye_rect.collidepoint(event.pos):
                    password_visible = not password_visible
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_box = 'password' if input_box == 'username' else 'username'
                elif event.key == pygame.K_ESCAPE:
                    return False, 'Возврат в главное меню.'
                elif event.key == pygame.K_RETURN:
                    if len(username) < 3 or len(password) < 6:
                        message = 'Имя пользователя ≥ 3 символа, пароль ≥ 6 символов.'
                    else:
                        success, msg = register(username, password)
                        if success:
                            message = 'Регистрация успешна. Можете войти.'
                        else:
                            message = msg
                elif event.key == pygame.K_BACKSPACE:
                    if input_box == 'username':
                        username = username[:-1]
                    else:
                        password = password[:-1]
                else:
                    if input_box == 'username' and event.unicode.isprintable():
                        username += event.unicode
                    elif input_box == 'password' and event.unicode.isprintable():
                        password += event.unicode
        clock.tick(settings.FPS)

# ---------- Экран выбора режима ----------
def select_mode(username):
    """
    После входа предлагает выбрать: игра с ИИ, просмотр текущих игр или выход.
    """
    message = ''
    while True:
        screen.fill(settings.BLACK)
        draw_text(screen, 'Выберите режим игры', 60, settings.WHITE, settings.WINDOW_WIDTH // 2 - 200, 50)
        draw_text(screen, '1. Человек против искусственного интеллекта', 40, settings.WHITE, 100, 200)
        draw_text(screen, '2. Просмотреть текущие игры', 40, settings.WHITE, 100, 300)
        draw_text(screen, '3. Выйти', 40, settings.WHITE, 100, 400)
        draw_text(screen, message, 30, settings.RED, 100, 500)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 'ai'
                if event.key == pygame.K_2:
                    view_games(username)
                if event.key == pygame.K_3:
                    pygame.quit()
                    sys.exit()
        clock.tick(settings.FPS)

def view_games(username):
    """
    Отображает список незавершённых партий пользователя.
    Можно выбрать партию для продолжения или вернуться назад.
    """
    games = get_games_by_user(username, status='in_progress')
    selected_game = None
    while True:
        screen.fill(settings.BLACK)
        draw_text(screen, f'Текущие партии пользователя: {username}', 40, settings.WHITE, settings.WINDOW_WIDTH // 2 - 250, 50)
        y_offset = 150
        if not games:
            draw_text(screen, 'Нет текущих партий. Начните новую игру.', 30, settings.WHITE, 50, y_offset)
        else:
            for index, game in enumerate(games[:10]):  # показываем последние 10
                game_id, white_player, black_player, moves, result, start_time, end_time, status = game
                game_info = f"{index + 1}. ID: {game_id} | Белые: {white_player} | Черные: {black_player} | Начало: {start_time}"
                draw_text(screen, game_info, 25, settings.WHITE, 50, y_offset)
                y_offset += 40
                if y_offset > settings.WINDOW_HEIGHT - 100:
                    break
        draw_text(screen, 'Нажмите число партии для возобновления или ESC для возврата', 25, settings.WHITE, 50, settings.WINDOW_HEIGHT - 100)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    selected_index = event.key - pygame.K_1
                    if selected_index < len(games):
                        selected_game = games[selected_index]
                        resume_game(selected_game)
        clock.tick(settings.FPS)

def resume_game(game):
    """
    Загружает выбранную партию и переходит в игровой экран.
    """
    game_id, white_player, black_player, moves, result, start_time, end_time, status = game
    game_instance = Game(white_player=white_player, black_player=black_player, game_id=game_id)
    game_screen_instance(game_instance)

# ---------- Игровой экран ----------
def game_screen_instance(game_instance):
    """
    Основной игровой цикл для одной партии.
    Обрабатывает события мыши и клавиатуры, вызывает отрисовку.
    """
    selected_square = None
    valid_moves = []
    run = True
    paused = False

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused    # пауза
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not paused and not game_instance.checkmate and not game_instance.stalemate:
                    pos = pygame.mouse.get_pos()
                    row, col = pos[1] // settings.CELL_SIZE, pos[0] // settings.CELL_SIZE
                    piece = game_instance.board.get_piece(row, col)

                    if selected_square:
                        # Если уже есть выбранная фигура, ищем ход в valid_moves
                        selected_move = None
                        for m in valid_moves:
                            if m.end_row == row and m.end_col == col:
                                selected_move = m
                                break

                        if selected_move and game_instance.is_move_valid(selected_move):
                            # Делаем ход
                            game_instance.make_move(selected_move)
                            selected_square = None
                            valid_moves = []

                            # Если после хода очередь перешла к AI, делаем ответный ход
                            if (isinstance(game_instance.black_player, str) and
                                    game_instance.black_player.lower() == 'ai' and
                                    not game_instance.white_to_move and
                                    not game_instance.checkmate and
                                    not game_instance.stalemate):
                                ai_move = find_best_move(game_instance, depth=settings.AI_DEPTH)
                                if ai_move:
                                    game_instance.make_move(ai_move)
                        else:
                            # Если ход неверный, проверяем, может быть выбрана другая фигура
                            if piece != '--' and ((game_instance.white_to_move and piece[0] == 'w') or
                                                  (not game_instance.white_to_move and piece[0] == 'b')):
                                selected_square = (row, col)
                                valid_moves = game_instance.get_piece_moves(row, col)
                            else:
                                selected_square = None
                                valid_moves = []
                    else:
                        # Нет выбранной фигуры – выбираем, если кликнули на свою фигуру
                        if piece != '--' and ((game_instance.white_to_move and piece[0] == 'w') or
                                              (not game_instance.white_to_move and piece[0] == 'b')):
                            selected_square = (row, col)
                            valid_moves = game_instance.get_piece_moves(row, col)

        if not paused:
            screen.fill(settings.BLACK)
            renderer.draw_game(game_instance, selected_square, valid_moves)
        else:
            # Экран паузы
            screen.fill(settings.GRAY)
            draw_text(screen, 'Пауза', 60, settings.WHITE, settings.WINDOW_WIDTH // 2 - 100, settings.WINDOW_HEIGHT // 2 - 50)
            draw_text(screen, 'Нажмите S для сохранения и выхода', 30, settings.WHITE, settings.WINDOW_WIDTH // 2 - 150, settings.WINDOW_HEIGHT // 2 + 20)
            draw_text(screen, 'Нажмите P для продолжения игры', 30, settings.WHITE, settings.WINDOW_WIDTH // 2 - 150, settings.WINDOW_HEIGHT // 2 + 60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        run = False      # сохранить и выйти
                    elif event.key == pygame.K_p:
                        paused = False

        pygame.display.flip()
        clock.tick(settings.FPS)

        # Если игра завершена (мат/пат), показываем результат и выходим
        if not paused and (game_instance.checkmate or game_instance.stalemate):
            pygame.time.delay(5000)
            run = False
            if game_instance.result:
                game_instance.save_game_completion()

def game_screen(mode, white_player='White', black_player='AI'):
    """
    Создаёт новую игру (или загружает существующую) и запускает игровой цикл.
    """
    if mode == 'ai':
        if black_player.lower() == 'ai':
            game_id = create_new_game(white_player, 'AI')
            game_instance = Game(white_player=white_player, black_player='AI', game_id=game_id)
        else:
            game_id = create_new_game(white_player, black_player)
            game_instance = Game(white_player=white_player, black_player=black_player, game_id=game_id)
    run_game = True
    while run_game:
        game_screen_instance(game_instance)
        run_game = False

# ---------- Точка входа ----------
def main():
    """Главная функция: инициализация БД, аутентификация, выбор режима."""
    initialize_db()
    current_user = auth_screen()
    if current_user:
        mode = select_mode(current_user)
        if mode == 'ai':
            game_screen(mode, white_player=current_user, black_player='AI')

if __name__ == '__main__':
    main()