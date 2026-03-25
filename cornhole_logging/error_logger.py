import csv
import os
from datetime import datetime
import traceback

class ErrorLogger:
    def __init__(self, filename="error_log.csv"):
        self.filename = filename
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "error", "traceback"])

    def log(self, error):
        ts = datetime.utcnow().isoformat()
        tb = traceback.format_exc()

        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, str(error), tb])
