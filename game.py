# game.py
# Модуль содержит класс Game, управляющий состоянием партии:
# очередность хода, проверка на шах/мат/пат, сохранение/загрузка игры,
# взаимодействие с базой данных и экспорт в PGN.

import pygame
import settings
from board import Board
from move import Move
from copy import deepcopy
from datetime import datetime
from database import update_game, get_game_by_id
import json

class Game:
    """
    Класс игры хранит всю информацию о текущей партии: игроков, доску,
    историю ходов, флаги окончания и результат.
    """

    def __init__(self, white_player='White', black_player='AI', game_id=None):
        """
        :param white_player: имя игрока белыми
        :param black_player: имя игрока чёрными (может быть 'AI')
        :param game_id: если передан, игра загружается из БД
        """
        self.board = Board()                     # объект доски
        self.white_player = white_player
        self.black_player = black_player
        self.game_id = game_id
        if game_id:
            self.load_game(game_id)              # загрузка существующей партии
        else:
            self.white_to_move = True             # сейчас ход белых
            self.move_log = []                     # список совершённых ходов (объекты Move)
            self.selected_square = None            # текущая выбранная клетка (для GUI)
            self.valid_moves = []                   # допустимые ходы для выбранной фигуры
            self.checkmate = False
            self.stalemate = False
            self.en_passant_possible = ()          # (не используется в данной версии)
            self.promotion_choice = 'Q'             # фигура по умолчанию при превращении
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.end_time = None
            self.result = None                       # строка с результатом

    # ---------- Загрузка/сохранение игры ----------
    def load_game(self, game_id):
        """Загружает партию из базы данных по её идентификатору."""
        game = get_game_by_id(game_id)
        if game:
            (_, white_player, black_player, moves, result,
             start_time, end_time, status) = game
            self.white_player = white_player
            self.black_player = black_player
            self.move_log = [Move.from_dict(move_dict) for move_dict in json.loads(moves)]
            self.reconstruct_board()
            self.result = result
            self.start_time = start_time
            self.end_time = end_time
            self.checkmate = status == 'completed' and (result and 'checkmate' in result.lower())
            self.stalemate = status == 'completed' and (result and 'stalemate' in result.lower())
            self.white_to_move = len(self.move_log) % 2 == 0   # чётное число ходов -> ход белых
        else:
            print(f"Игра с ID {game_id} не найдена. Создаётся новая.")
            # Сброс всех полей
            self.board = Board()
            self.white_to_move = True
            self.move_log = []
            self.selected_square = None
            self.valid_moves = []
            self.checkmate = False
            self.stalemate = False
            self.en_passant_possible = ()
            self.promotion_choice = 'Q'
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.end_time = None
            self.result = None

    def reconstruct_board(self):
        """Восстанавливает позицию на доске, последовательно применяя ходы из move_log."""
        self.board = Board()
        for move in self.move_log:
            self.board.set_piece(move.start_row, move.start_col, '--')
            self.board.set_piece(move.end_row, move.end_col, move.piece_moved)
            if move.is_pawn_promotion:
                self.board.set_piece(move.end_row, move.end_col,
                                     move.piece_moved[0] + move.promotion_choice)

    # ---------- Получение допустимых ходов ----------
    def get_valid_moves(self):
        """
        Возвращает список допустимых ходов для текущего игрока.
        Отсеивает ходы, после которых свой король оказывается под шахом.
        """
        color = 'w' if self.white_to_move else 'b'
        raw_moves = self.board.get_all_possible_moves(color)
        valid = []
        for move in raw_moves:
            # Создаём копию игры, делаем ход и проверяем, не под шахом ли наш король
            game_copy = deepcopy(self)
            game_copy.make_move(move, update_state=False)
            if not game_copy.in_check(not self.white_to_move):
                valid.append(move)
        return valid

    # ---------- Выполнение и отмена хода ----------
    def make_move(self, move, update_state=True):
        """
        Выполняет ход на доске, добавляет его в лог, переключает очередь.
        :param move: объект Move
        :param update_state: если True, после хода проверяется состояние игры и сохраняется в БД
        """
        self.board.set_piece(move.start_row, move.start_col, '--')
        self.board.set_piece(move.end_row, move.end_col, move.piece_moved)
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move
        if move.is_pawn_promotion:
            self.board.set_piece(move.end_row, move.end_col,
                                 move.piece_moved[0] + move.promotion_choice)
        if update_state:
            self.check_game_state()
            self.save_current_game()

    def undo_move(self):
        """Отменяет последний ход (восстанавливает взятую фигуру и очередь)."""
        if self.move_log:
            move = self.move_log.pop()
            self.board.set_piece(move.start_row, move.start_col, move.piece_moved)
            self.board.set_piece(move.end_row, move.end_col, move.piece_captured)
            self.white_to_move = not self.white_to_move
            self.check_game_state()
            self.save_current_game()

    # ---------- Проверка шаха и атак ----------
    def in_check(self, white_to_move):
        """
        Проверяет, находится ли король указанного цвета под шахом.
        :param white_to_move: True – проверяем белого короля, False – чёрного.
        """
        color = 'w' if white_to_move else 'b'
        king_pos = None
        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece(r, c)
                if piece != '--' and piece[0] == color and piece[1] == 'K':
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        if king_pos is None:
            return True   # король отсутствует (считаем шахом для безопасности)
        return self.is_square_under_attack(king_pos[0], king_pos[1],
                                           'b' if white_to_move else 'w')

    def is_square_under_attack(self, row, col, attacker_color):
        """
        Проверяет, атакована ли клетка (row, col) фигурами цвета attacker_color.
        Учитываются все виды фигур.
        """
        # Пешки
        direction = -1 if attacker_color == 'w' else 1
        for dc in [-1, 1]:
            r = row + direction
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board.get_piece(r, c)
                if piece != '--' and piece[0] == attacker_color and piece[1] == 'P':
                    return True

        # Кони
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                        (1, -2), (2, -1), (1, 2), (2, 1)]
        for dr, dc in knight_moves:
            r = row + dr
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board.get_piece(r, c)
                if piece != '--' and piece[0] == attacker_color and piece[1] == 'N':
                    return True

        # Ладьи и ферзи (горизонталь/вертикаль)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = self.board.get_piece(r, c)
                if piece == '--':
                    r += dr
                    c += dc
                    continue
                if piece[0] == attacker_color:
                    if piece[1] in ['R', 'Q']:
                        return True
                    else:
                        break
                else:
                    break

        # Слоны и ферзи (диагональ)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = self.board.get_piece(r, c)
                if piece == '--':
                    r += dr
                    c += dc
                    continue
                if piece[0] == attacker_color:
                    if piece[1] in ['B', 'Q']:
                        return True
                    else:
                        break
                else:
                    break

        # Король
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = self.board.get_piece(r, c)
                if piece != '--' and piece[0] == attacker_color and piece[1] == 'K':
                    return True

        return False

    # ---------- Определение окончания игры ----------
    def check_game_state(self):
        """
        Проверяет, есть ли мат, пат или ничья из-за недостатка материала,
        и устанавливает соответствующие флаги и результат.
        """
        if self.in_check(self.white_to_move):
            if not self.get_valid_moves():
                self.checkmate = True
                self.stalemate = False
                self.result = ('Black wins by checkmate' if self.white_to_move
                               else 'White wins by checkmate')
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                self.checkmate = False
                self.stalemate = False
        else:
            if not self.get_valid_moves():
                self.stalemate = True
                self.checkmate = False
                self.result = 'Draw by stalemate'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            elif self.is_only_kings():
                self.stalemate = True
                self.result = 'Draw by insufficient material'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                self.stalemate = False
                self.checkmate = False

    def is_only_kings(self):
        """Проверяет, остались ли на доске только короли."""
        for r in range(8):
            for c in range(8):
                piece = self.board.get_piece(r, c)
                if piece != '--' and piece[1] != 'K':
                    return False
        return True

    # ---------- Работа с базой данных ----------
    def update_game_status(self, status):
        """Обновляет статус партии в БД (in_progress/completed)."""
        if self.game_id:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status=status
            )

    def save_current_game(self):
        """Сохраняет текущее состояние партии в БД."""
        if self.game_id:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status='completed' if self.result else 'in_progress'
            )

    def save_game_completion(self):
        """Сохраняет завершённую партию и экспортирует её в PGN."""
        if self.game_id and self.result:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status='completed'
            )
            self.export_pgn()

    def export_pgn(self):
        """
        Экспортирует партию в формат PGN (Portable Game Notation).
        Создаёт текстовый файл с метаданными и последовательностью ходов.
        """
        if not self.game_id:
            return
        pgn_content = f"[Event \"Chess Endgame\"]\n"
        pgn_content += f"[Site \"Local\"]\n"
        pgn_content += f"[Date \"{self.start_time.split(' ')[0]}\"]\n"
        pgn_content += f"[Round \"-\"]\n"
        pgn_content += f"[White \"{self.white_player}\"]\n"
        pgn_content += f"[Black \"{self.black_player}\"]\n"
        pgn_content += f"[Result \"{self.result}\"]\n\n"

        move_text = ''
        for i in range(0, len(self.move_log), 2):
            move_number = i // 2 + 1
            white_move = self.move_log[i].get_chess_notation()
            black_move = self.move_log[i + 1].get_chess_notation() if i + 1 < len(self.move_log) else ''
            move_text += f"{move_number}. {white_move} {black_move} "

        move_text += self.result
        pgn_content += move_text

        pgn_filename = f"game_{self.start_time.replace(':', '-').replace(' ', '_')}_id_{self.game_id}.pgn"
        with open(pgn_filename, 'w') as f:
            f.write(pgn_content)

    # ---------- Вспомогательные методы для GUI ----------
    def get_piece_moves(self, r, c):
        """
        Возвращает допустимые ходы для фигуры в клетке (r,c).
        Используется при выборе фигуры игроком.
        """
        piece = self.board.get_piece(r, c)
        if piece == '--':
            return []
        if self.white_to_move and piece[0] != 'w':
            return []
        if not self.white_to_move and piece[0] != 'b':
            return []
        # Генерируем все возможные ходы этой фигуры (без учёта шаха)
        moves = []
        ptype = piece[1]
        color = piece[0]
        if ptype == 'K':
            self.board._get_king_moves(r, c, color, moves)
        elif ptype == 'Q':
            self.board._get_queen_moves(r, c, color, moves)
        elif ptype == 'R':
            self.board._get_rook_moves(r, c, color, moves)
        elif ptype == 'B':
            self.board._get_bishop_moves(r, c, color, moves)
        elif ptype == 'N':
            self.board._get_knight_moves(r, c, color, moves)
        elif ptype == 'P':
            self.board._get_pawn_moves(r, c, color, moves)

        # Отфильтровываем те, после которых король остаётся под шахом
        valid = []
        for move in moves:
            game_copy = deepcopy(self)
            game_copy.make_move(move, update_state=False)
            if not game_copy.in_check(not self.white_to_move):
                valid.append(move)
        return valid

    def is_move_valid(self, move):
        """Проверяет, входит ли данный ход в список допустимых."""
        return move in self.get_valid_moves()