import csv
import os
from datetime import datetime

class RoundLogger:
    def __init__(self, filename="round_log.csv"):
        self.filename = filename
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "round",
                    "round_hits_p1",
                    "round_hits_p2",
                    "total_score_p1",
                    "total_score_p2",
                    "accuracy_p1",
                    "accuracy_p2"
                ])

    def log(self, game):
        ts = datetime.utcnow().isoformat()

        acc_p1, acc_p2 = game.get_accuracy()

        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                game.round_number,
                game.round_hits_p1,
                game.round_hits_p2,
                game.total_score_p1,
                game.total_score_p2,
                f"{acc_p1:.2f}",
                f"{acc_p2:.2f}"
            ])