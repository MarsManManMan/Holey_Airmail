import csv
import os
from datetime import datetime

class DetectionLogger:
    def __init__(self, filename="detection_log.csv"):
        self.filename = filename
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "bag_id",
                    "color",
                    "x",
                    "y",
                    "movement",
                    "still_frames",
                    "on_board",
                    "in_hole"
                ])

    def log(self, bag, on_board, in_hole):
        ts = datetime.utcnow().isoformat()

        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                bag["id"],
                bag["color"],
                bag["centroid"][0],
                bag["centroid"][1],
                round(bag["movement"], 4),
                bag.get("still_frames", 0),
                int(on_board),
                int(in_hole),
            ])