import json
import os
from datetime import datetime

class JSONLogger:
    def __init__(self, filename="event_log.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump([], f, indent=4)

    def log(self, event, game=None, player=None, color=None, points=0):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "player": player,
            "color": color,
            "points": points,
            "total_score_p1": game.total_score_p1 if game else None,
            "total_score_p2": game.total_score_p2 if game else None,
            "round": game.round_number if game else None
        }

        with open(self.filename, "r") as f:
            data = json.load(f)

        data.append(entry)

        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)