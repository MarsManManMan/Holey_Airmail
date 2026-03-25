import csv
import os
from datetime import datetime

class EventLogger:
    def __init__(self, filename="event_log.csv"):
        self.filename = filename
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "event",
                    "player",
                    "color",
                    "points",
                    "total_score_p1",
                    "total_score_p2",
                    "round"
                ])

    def log(self, event, game=None, player=None, color=None, points=0):
        ts = datetime.utcnow().isoformat()

        total_p1 = game.total_score_p1 if game else ""
        total_p2 = game.total_score_p2 if game else ""
        round_nr = game.round_number if game else ""

        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                event,
                player or "",
                color or "",
                points,
                total_p1,
                total_p2,
                round_nr
            ])