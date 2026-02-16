# renderer.py
# Модуль отвечает за визуализацию шахматной доски, фигур и состояния игры.
# Использует библиотеку Pygame.

import pygame
import settings

class GameRenderer:
    """
    Класс для отрисовки всех элементов игры на экране.
    Хранит ссылку на экран и словарь загруженных изображений.
    """

    def __init__(self, screen, images):
        """
        :param screen: поверхность Pygame, на которой будет рисование
        :param images: словарь с изображениями фигур и интерфейса
        """
        self.screen = screen
        self.images = images

    def draw_game(self, game, selected_square=None, valid_moves=None):
        """
        Основной метод отрисовки: вызывает последовательно отрисовку доски,
        фигур и состояния игры.
        """
        self._draw_board(game, selected_square, valid_moves)
        self._draw_pieces(game)
        self._draw_game_state(game)

    def _draw_board(self, game, selected_square, valid_moves):
        """
        Рисует шахматную доску: клетки чередующихся цветов,
        подсвечивает выбранную клетку синей рамкой,
        отмечает допустимые ходы зелёными кружками.
        """
        colors = [settings.WHITE, settings.GRAY]
        for r in range(settings.BOARD_SIZE):
            for c in range(settings.BOARD_SIZE):
                color = colors[(r + c) % 2]
                pygame.draw.rect(self.screen, color,
                                 (c * settings.CELL_SIZE, r * settings.CELL_SIZE,
                                  settings.CELL_SIZE, settings.CELL_SIZE))

                # Если клетка выбрана, обводим её синей рамкой
                if selected_square and (r, c) == selected_square:
                    pygame.draw.rect(self.screen, settings.BLUE,
                                     (c * settings.CELL_SIZE, r * settings.CELL_SIZE,
                                      settings.CELL_SIZE, settings.CELL_SIZE), 3)

                # Если для выбранной фигуры есть допустимые ходы, отмечаем конечные клетки
                if valid_moves:
                    for move in valid_moves:
                        if move.end_row == r and move.end_col == c:
                            center = (c * settings.CELL_SIZE + settings.CELL_SIZE // 2,
                                      r * settings.CELL_SIZE + settings.CELL_SIZE // 2)
                            pygame.draw.circle(self.screen, settings.GREEN, center, 10)

    def _draw_pieces(self, game):
        """Размещает изображения фигур на соответствующих клетках."""
        for r in range(settings.BOARD_SIZE):
            for c in range(settings.BOARD_SIZE):
                piece = game.board.get_piece(r, c)
                if piece != '--':
                    img = self.images.get(piece)
                    if img:
                        self.screen.blit(img, (c * settings.CELL_SIZE, r * settings.CELL_SIZE))
                    else:
                        print(f"Изображение для {piece} не найдено.")

    def _draw_game_state(self, game):
        """
        Выводит сообщения о шахе, мате или пате на экран.
        """
        if game.checkmate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Шах и мат!', True, settings.RED)
            self.screen.blit(text, (settings.WINDOW_WIDTH // 2 - text.get_width() // 2,
                                    settings.WINDOW_HEIGHT // 2 - text.get_height() // 2))
        elif game.stalemate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Пат!', True, settings.RED)
            self.screen.blit(text, (settings.WINDOW_WIDTH // 2 - text.get_width() // 2,
                                    settings.WINDOW_HEIGHT // 2 - text.get_height() // 2))
        elif game.in_check(game.white_to_move):
            font = pygame.font.SysFont('Arial', 24)
            text = font.render('Шах!', True, settings.RED)
            self.screen.blit(text, (10, 10))