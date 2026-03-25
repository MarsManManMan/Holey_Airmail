# detection.py
import cv2
import numpy as np
import time
from collections import deque
from config import COLOR_RANGES, MIN_BAG_AREA, MAX_BAG_DISTANCE, COOLDOWN_SECONDS

class BagTracker:
    def __init__(self):
        self.next_id = 1
        self.bags = {}  # id -> {id, color, centroid, last_seen, last_scored_time}

    def _distance(self, p1, p2):
        return np.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def update(self, detections):
        # detections: list of dicts {color, centroid, contour, mean_hsv}
        now = time.time()
        updated_ids = set()

        for det in detections:
            c = det["centroid"]
            color = det["color"]  # op basis van range, kan later dominant color gebruiken

            # match met bestaande bag
            best_id = None
            best_dist = 1e9

            for bid, b in self.bags.items():
                d = self._distance(c, b["centroid"])
                if d < best_dist and d <= MAX_BAG_DISTANCE:
                    best_dist = d
                    best_id = bid

            if best_id is not None:
                # update
                self.bags[best_id]["centroid"] = c
                self.bags[best_id]["color"] = color
                self.bags[best_id]["last_seen"] = now
                updated_ids.add(best_id)
                det["id"] = best_id
            else:
                # nieuwe bag
                bid = self.next_id
                self.next_id += 1
                self.bags[bid] = {
                    "id": bid,
                    "centroid": c,
                    "color": color,
                    "last_seen": now,
                    "last_scored_time": 0.0
                }
                updated_ids.add(bid)
                det["id"] = bid

        # oude bags opruimen
        to_delete = []
        for bid, b in self.bags.items():
            if now - b["last_seen"] > 10.0:
                to_delete.append(bid)
        for bid in to_delete:
            del self.bags[bid]

        return detections

    def can_score(self, bag_id):
        now = time.time()
        b = self.bags.get(bag_id)
        if not b:
            return False
        if now - b["last_scored_time"] >= COOLDOWN_SECONDS:
            self.bags[bag_id]["last_scored_time"] = now
            return True
        return False


def compute_dominant_color_hsv(hsv_frame, contour):
    mask = np.zeros(hsv_frame.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    pixels = hsv_frame[mask == 255]
    if len(pixels) == 0:
        return None
    mean = np.mean(pixels, axis=0)
    return tuple(mean.astype(int))


def detect_bags(frame, active_colors):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    kernel = np.ones((5, 5), np.uint8)

    detections = []

    for color_name in active_colors:
        lower, upper = COLOR_RANGES[color_name]
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_BAG_AREA:
                continue

            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            mean_hsv = compute_dominant_color_hsv(hsv, cnt)

            detections.append({
                "color": color_name,
                "centroid": (cx, cy),
                "area": area,
                "contour": cnt,
                "mean_hsv": mean_hsv,
            })

    return detections
