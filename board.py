# board.py
# Модуль отвечает за хранение состояния доски и генерацию всех возможных ходов
# для каждой фигуры без учёта шаха.

import settings
from move import Move

class Board:
    """
    Класс доски: хранит двумерный список grid с фигурами,
    предоставляет методы для получения/установки фигуры и
    генерации всех потенциальных ходов для заданного цвета.
    """

    def __init__(self):
        """Инициализация доски начальной расстановкой для эндшпиля."""
        self.grid = self._create_initial_board()

    def _create_initial_board(self):
        """
        Создаёт начальную позицию: два короля и две пешки.
        Белые: король на e1 (7,4), пешка на a2 (6,0)
        Чёрные: король на e8 (0,4), пешка на h7 (1,7)
        """
        board = [['--' for _ in range(settings.BOARD_SIZE)] for _ in range(settings.BOARD_SIZE)]
        board[7][4] = 'wK'
        board[6][0] = 'wP'
        board[0][4] = 'bK'
        board[1][7] = 'bP'
        return board

    def get_piece(self, row, col):
        """Возвращает фигуру в клетке (row, col) или '--', если клетка пуста."""
        return self.grid[row][col]

    def set_piece(self, row, col, piece):
        """Устанавливает фигуру в указанную клетку."""
        self.grid[row][col] = piece

    def get_all_possible_moves(self, color):
        """
        Возвращает список всех возможных ходов для фигур указанного цвета
        без проверки на шах.
        :param color: 'w' или 'b'
        """
        moves = []
        for r in range(settings.BOARD_SIZE):
            for c in range(settings.BOARD_SIZE):
                piece = self.grid[r][c]
                if piece != '--' and piece[0] == color:
                    ptype = piece[1]
                    if ptype == 'K':
                        self._get_king_moves(r, c, color, moves)
                    elif ptype == 'Q':
                        self._get_queen_moves(r, c, color, moves)
                    elif ptype == 'R':
                        self._get_rook_moves(r, c, color, moves)
                    elif ptype == 'B':
                        self._get_bishop_moves(r, c, color, moves)
                    elif ptype == 'N':
                        self._get_knight_moves(r, c, color, moves)
                    elif ptype == 'P':
                        self._get_pawn_moves(r, c, color, moves)
        return moves

    # ---------- Генерация ходов для каждой фигуры ----------
    def _get_pawn_moves(self, r, c, color, moves):
        """
        Добавляет в список moves все возможные ходы пешки из клетки (r,c).
        Учитывает движение на 1 и 2 клетки, взятие по диагонали и превращение.
        """
        direction = -1 if color == 'w' else 1
        start_row = 6 if color == 'w' else 1
        enemy = 'b' if color == 'w' else 'w'

        # ход на 1 клетку вперёд
        if 0 <= r + direction < 8 and self.grid[r + direction][c] == '--':
            # проверка на достижение последнего ряда (превращение)
            if (color == 'w' and r + direction == 0) or (color == 'b' and r + direction == 7):
                for promo in ['Q', 'R', 'B', 'N']:
                    moves.append(Move((r, c), (r + direction, c), self.grid[r][c], '--',
                                      is_pawn_promotion=True, promotion_choice=promo))
            else:
                moves.append(Move((r, c), (r + direction, c), self.grid[r][c], '--'))
            # ход на 2 клетки из начального положения
            if r == start_row and self.grid[r + 2 * direction][c] == '--':
                moves.append(Move((r, c), (r + 2 * direction, c), self.grid[r][c], '--'))

        # взятие по диагонали (влево и вправо)
        for dc in [-1, 1]:
            if 0 <= c + dc < 8 and 0 <= r + direction < 8:
                target = self.grid[r + direction][c + dc]
                if target != '--' and target[0] == enemy:
                    if (color == 'w' and r + direction == 0) or (color == 'b' and r + direction == 7):
                        for promo in ['Q', 'R', 'B', 'N']:
                            moves.append(Move((r, c), (r + direction, c + dc), self.grid[r][c], target,
                                              is_pawn_promotion=True, promotion_choice=promo))
                    else:
                        moves.append(Move((r, c), (r + direction, c + dc), self.grid[r][c], target))

    def _get_king_moves(self, r, c, color, moves):
        """Добавляет все возможные ходы короля (без учёта шаха, только перемещения)."""
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]
        for dr, dc in directions:
            end_r, end_c = r + dr, c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                target = self.grid[end_r][end_c]
                if target == '--' or target[0] != color:
                    moves.append(Move((r, c), (end_r, end_c), self.grid[r][c], target))

    def _get_queen_moves(self, r, c, color, moves):
        """Ходы ферзя = ходы ладьи + слона."""
        self._get_rook_moves(r, c, color, moves)
        self._get_bishop_moves(r, c, color, moves)

    def _get_rook_moves(self, r, c, color, moves):
        """Добавляет все возможные ходы ладьи по горизонтали и вертикали."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            end_r, end_c = r + dr, c + dc
            while 0 <= end_r < 8 and 0 <= end_c < 8:
                target = self.grid[end_r][end_c]
                if target == '--':
                    moves.append(Move((r, c), (end_r, end_c), self.grid[r][c], target))
                else:
                    if target[0] != color:
                        moves.append(Move((r, c), (end_r, end_c), self.grid[r][c], target))
                    break
                end_r += dr
                end_c += dc

    def _get_bishop_moves(self, r, c, color, moves):
        """Добавляет все возможные ходы слона по диагоналям."""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            end_r, end_c = r + dr, c + dc
            while 0 <= end_r < 8 and 0 <= end_c < 8:
                target = self.grid[end_r][end_c]
                if target == '--':
                    moves.append(Move((r, c), (end_r, end_c), self.grid[r][c], target))
                else:
                    if target[0] != color:
                        moves.append(Move((r, c), (end_r, end_c), self.grid[r][c], target))
                    break
                end_r += dr
                end_c += dc

    def _get_knight_moves(self, r, c, color, moves):
        """Добавляет все возможные ходы коня."""
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                        (1, -2), (2, -1), (1, 2), (2, 1)]
        for dr, dc in knight_moves:
            end_r, end_c = r + dr, c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                target = self.grid[end_r][end_c]
                if target == '--' or target[0] != color:
                    moves.append(Move((r, c), (end_r, end_c), self.grid[r][c], target))