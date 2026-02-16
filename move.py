# move.py
# Модуль описывает класс Move, представляющий один ход в шахматах.

class Move:
    """
    Класс, хранящий информацию о ходе: начальная и конечная позиция,
    какая фигура была перемещена, какая взята, а также флаг превращения пешки.
    """

    def __init__(self, start_pos, end_pos, piece_moved, piece_captured,
                 is_pawn_promotion=False, promotion_choice='Q'):
        """
        :param start_pos: кортеж (ряд, колонка) начальной клетки
        :param end_pos: кортеж (ряд, колонка) конечной клетки
        :param piece_moved: строка, обозначающая фигуру (например 'wP')
        :param piece_captured: строка обозначения взятой фигуры или '--'
        :param is_pawn_promotion: True, если ход приводит к превращению пешки
        :param promotion_choice: выбранная фигура при превращении ('Q','R','B','N')
        """
        self.start_row, self.start_col = start_pos
        self.end_row, self.end_col = end_pos
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        self.is_pawn_promotion = is_pawn_promotion
        self.promotion_choice = promotion_choice

    def __eq__(self, other):
        """Перегрузка оператора сравнения для возможности поиска хода в списке."""
        if isinstance(other, Move):
            return (self.start_row == other.start_row and
                    self.start_col == other.start_col and
                    self.end_row == other.end_row and
                    self.end_col == other.end_col and
                    self.piece_moved == other.piece_moved and
                    self.piece_captured == other.piece_captured and
                    self.is_pawn_promotion == other.is_pawn_promotion and
                    self.promotion_choice == other.promotion_choice)
        return False

    def get_chess_notation(self):
        """
        Возвращает строковое представление хода в шахматной нотации
        (например, 'e2e4').
        """
        cols_to_files = {0: 'a', 1: 'b', 2: 'c', 3: 'd',
                         4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        return (cols_to_files[self.start_col] + str(8 - self.start_row) +
                cols_to_files[self.end_col] + str(8 - self.end_row))

    def to_dict(self):
        """Преобразует ход в словарь для сохранения в JSON."""
        return {
            'start_pos': [self.start_row, self.start_col],
            'end_pos': [self.end_row, self.end_col],
            'piece_moved': self.piece_moved,
            'piece_captured': self.piece_captured,
            'is_pawn_promotion': self.is_pawn_promotion,
            'promotion_choice': self.promotion_choice
        }

    @classmethod
    def from_dict(cls, move_dict):
        """Создаёт объект Move из словаря (загрузка из JSON)."""
        return cls(
            start_pos=tuple(move_dict['start_pos']),
            end_pos=tuple(move_dict['end_pos']),
            piece_moved=move_dict['piece_moved'],
            piece_captured=move_dict['piece_captured'],
            is_pawn_promotion=move_dict['is_pawn_promotion'],
            promotion_choice=move_dict.get('promotion_choice', 'Q')
        )