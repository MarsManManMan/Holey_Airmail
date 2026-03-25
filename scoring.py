# scoring.py
from config import POINTS_BOARD, POINTS_HOLE, TARGET_SCORE, WIN_BY_TWO

class CornholeGame:
    def __init__(self, player1_colors, player2_colors):
        self.player1_colors = player1_colors
        self.player2_colors = player2_colors

        self.reset_scores()

    def reset_scores(self):
        self.round_number = 1
        self.bags_per_round = 4

        self.round_hits_p1 = 0
        self.round_hits_p2 = 0

        self.total_score_p1 = 0
        self.total_score_p2 = 0

        self.total_bags_p1 = 0
        self.total_bags_p2 = 0

        self.made_points_p1 = 0
        self.made_points_p2 = 0

        self.game_over = False
        self.winner = None

    def register_hit(self, color, is_hole):
        if self.game_over:
            return

        points = POINTS_HOLE if is_hole else POINTS_BOARD

        # wie krijgt de punten?
        if color in self.player1_colors:
            self.round_hits_p1 += points
            self.total_bags_p1 += 1
            self.made_points_p1 += points
        elif color in self.player2_colors:
            self.round_hits_p2 += points
            self.total_bags_p2 += 1
            self.made_points_p2 += points

    def end_round(self):
        # netto score toepassen
        diff = self.round_hits_p1 - self.round_hits_p2
        if diff > 0:
            self.total_score_p1 += diff
        elif diff < 0:
            self.total_score_p2 += -diff

        # check win
        if self.total_score_p1 >= TARGET_SCORE or self.total_score_p2 >= TARGET_SCORE:
            if not WIN_BY_TWO or abs(self.total_score_p1 - self.total_score_p2) >= 2:
                self.game_over = True
                self.winner = 1 if self.total_score_p1 > self.total_score_p2 else 2

        # reset ronde data
        self.round_hits_p1 = 0
        self.round_hits_p2 = 0
        self.round_number += 1

    def get_accuracy(self):
        acc1 = (self.made_points_p1 / (self.total_bags_p1 * POINTS_HOLE)
                * 100) if self.total_bags_p1 > 0 else 0
        acc2 = (self.made_points_p2 / (self.total_bags_p2 * POINTS_HOLE)
                * 100) if self.total_bags_p2 > 0 else 0
        return acc1, acc2
