# ai.py
# Модуль реализует алгоритм минимакса с альфа-бета отсечением для выбора лучшего хода.
# Также содержит простую оценочную функцию на основе материального преимущества.

import math
import random
import settings

def find_best_move(game, depth):
    """
    Находит лучший ход для текущего игрока.
    :param game: объект игры
    :param depth: глубина поиска
    :return: объект Move или None, если ходов нет
    """
    best_move = None
    if game.white_to_move:
        best_value = -math.inf
        candidates = []   # список ходов с одинаковой лучшей оценкой
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, False)
            game.undo_move()
            if move_value > best_value:
                best_value = move_value
                candidates = [move]
            elif move_value == best_value:
                candidates.append(move)
        if candidates:
            best_move = random.choice(candidates)   # случайный выбор среди равных
    else:
        best_value = math.inf
        candidates = []
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, True)
            game.undo_move()
            if move_value < best_value:
                best_value = move_value
                candidates = [move]
            elif move_value == best_value:
                candidates.append(move)
        if candidates:
            best_move = random.choice(candidates)

    print(f"AI выбрал ход: {best_move.get_chess_notation() if best_move else 'Нет доступных ходов'}")
    return best_move

def minimax(game, depth, alpha, beta, is_maximizing):
    """
    Рекурсивный алгоритм минимакса с альфа-бета отсечением.
    :param game: объект игры
    :param depth: оставшаяся глубина
    :param alpha: лучшее значение для максимизирующего игрока
    :param beta: лучшее значение для минимизирующего игрока
    :param is_maximizing: True, если текущий уровень максимизирует оценку
    :return: численная оценка позиции
    """
    if depth == 0 or game.checkmate or game.stalemate:
        return evaluate_game(game)

    if is_maximizing:
        max_eval = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, False)
            game.undo_move()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break   # отсечение
        return max_eval
    else:
        min_eval = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, True)
            game.undo_move()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break   # отсечение
        return min_eval

def evaluate_game(game):
    """
    Оценка позиции: разница в материале (белые - чёрные).
    Король имеет ценность 0.
    """
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    white_score = 0
    black_score = 0

    for row in game.board.grid:
        for piece in row:
            if piece != '--':
                value = piece_values.get(piece[1], 0)
                if piece[0] == 'w':
                    white_score += value
                else:
                    black_score += value

    evaluation = white_score - black_score
    print(f"Оценка позиции: {evaluation} (Белые: {white_score}, Черные: {black_score})")
    return evaluation