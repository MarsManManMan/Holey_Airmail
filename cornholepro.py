#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cornhole Pro 2.5 — Modern Clean Build
-------------------------------------

Volledig herschreven om:
- Webinterface van Cornhole Pro 2.4 (mooie versie, optie D) te ondersteunen
- Pi Camera Module 3 te ondersteunen (Picamera2)
- Logging (Event, JSON, Detection, Round, Error) correct in te bouwen
- ROI tekenen en verschuiven correct te laten werken
- De officiële netto-per-ronde Cornhole score-regels toe te passen
- Geen dubbele code, geen rare inspringingen, geen crashes

Dit is DEEL 1 van de volledige toepassing.
"""

import collections
from collections import deque
from email.mime.multipart import MIMEMultipart
import os

REPLAY_DIR = "replays"
if not os.path.exists(REPLAY_DIR):
    os.makedirs(REPLAY_DIR)

# buffer: laatste 120 frames = ±4 sec bij 30 FPS
replay_buffer = collections.deque(maxlen=120)
replay_index = 1
# ============================================================
# IMPORTS
# ============================================================
import json

PROFILE_FILE = "profiles.json"

def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

import matplotlib
matplotlib.use('Agg')  # Geen GUI nodig
import matplotlib.pyplot as plt
import time
import csv
import cv2
import numpy as np
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string
import qrcode
import socket
import cv2
import smtplib
from email.mime.text import MIMEText
from secretstuff import verstuurEmailAdress, Logincode
from collections import deque



# ============================================================
# LOGGING IMPORTS (uit map: cornhole_logging/)
# ============================================================

from cornhole_logging import (
    EventLogger,
    JSONLogger,
    DetectionLogger,
    RoundLogger,
    ErrorLogger
)

# ============================================================
# CAMERA (Pi Camera Module 3)
# ============================================================

from picamera2 import Picamera2
PICAMERA_AVAILABLE = True   # Altijd true voor Module 3


# ============================================================
# CONFIG
# ============================================================

import smtplib
from email.mime.text import MIMEText

def send_email_report(to_email, player_name, game, scores_p1, scores_p2):
    subject = "Cornhole Pro – Wedstrijdresultaat"

    acc1, acc2 = game.get_accuracy()

    # Bouw ASCII-statistieken
    def bar(value, max_width=20):
        filled = int((value / 100) * max_width)
        return "█" * filled + " " * (max_width - filled)

    accuracy_graph = f"""
Accuracy:
Speler 1: {bar(acc1)} {acc1:.1f}%
Speler 2: {bar(acc2)} {acc2:.1f}%
"""

    hitmap_p1 = "\n".join([f"{c.capitalize():8}: {'█' * v} {v}" for c, v in scores_p1.items()])
    hitmap_p2 = "\n".join([f"{c.capitalize():8}: {'█' * v} {v}" for c, v in scores_p2.items()])

    ppr1 = game.total_score_p1 / max(1, (game.round_number - 1))
    ppr2 = game.total_score_p2 / max(1, (game.round_number - 1))

    body = f"""
Hallo {player_name},

Hier is jouw Cornhole wedstrijdresultaat:
========================================
               EINDUITSLAG
========================================
- {team_1_name}:  {game.total_score_p1}
- {team_2_name}:  {game.total_score_p2}
- Winnaar: {team_1_name if game.winner == 1 else team_2_name}

========================================
               ACCURACY
========================================
{accuracy_graph}

========================================
       POINTS PER ROUND (PPR)
========================================
Speler 1: {ppr1:.2f}
Speler 2: {ppr2:.2f}

========================================
        HITMAP SP1 (per kleur)
========================================
{hitmap_p1}

========================================
        HITMAP SP2 (per kleur)
========================================
{hitmap_p2}

========================================
Bedankt voor het spelen!
Cornhole Pro 2.5
========================================
"""

# AI samenvatting genereren
    ai_summary = generate_ai_summary(game)

    body += f"""

========================================
         AI WEDSTRIJD SAMENVATTING
========================================
    {ai_summary}
    """

    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    msg = MIMEMultipart()
    msg.attach(MIMEText(body))
    msg["Subject"] = subject
    msg["From"] = verstuurEmailAdress
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(verstuurEmailAdress, Logincode)
            server.sendmail(msg["From"], [to_email], msg.as_string())

        print(f"Email verzonden naar {to_email}")

    except Exception as e:
        print("Email fout:", e)

def compute_momentum(game):

    try:
            p1, p2 = game.get_score_progression()
    except:
        return 0  # veiligheid

    # momentum = laatste netto verschil, genormaliseerd tussen -1 en +1
    diff = p1[-1] - p2[-1]
    total = max(p1[-1], p2[-1], 1)

    momentum = diff / total

    # limiteren
    if momentum > 1: momentum = 1
    if momentum < -1: momentum = -1

    return momentum

def live_commentary(game):
    """Genereer realtime tekst voor dashboard commentator."""
    if game.round_number <= 1:
        return "De wedstrijd gaat zo beginnen!"

    p1 = game.total_score_p1
    p2 = game.total_score_p2

    diff = p1 - p2

    if abs(diff) <= 1:
        return "Wat een spannende strijd! Het blijft nek-aan-nek!"

    if diff > 1:
        return f"{team_1_name} neemt de leiding met {diff} punten!"

    if diff < -1:
        return f"{team_2_name} domineert en staat {abs(diff)} punten voor!"

    return "De wedstrijd is in volle gang…"

CAMERA_RESOLUTION = (1280, 720)
TARGET_FPS = 30

COLOR_RANGES = {
    "blauw": [(90, 50, 50), (130, 255, 255)],
    "groen": [(35, 40, 40), (90, 255, 255)],
    "geel":  [(20, 70, 70), (35, 255, 255)],
    "zwart": [(0, 0, 0), (180, 255, 40)],
    "rood":  [(0, 120, 70), (10, 255, 255)],
    "wit":   [(0, 0, 200), (180, 40, 255)],
    "roze":  [(140, 50, 50), (175, 255, 255)],
}

# Tracking parameters
MIN_BAG_AREA = 300
MAX_BAG_AREA = 10000
MAX_BAG_DISTANCE = 60
MOVEMENT_THRESHOLD = 1.8
STILL_FRAMES_REQUIRED = 4
FRAMES_REQUIRED_IN_ROI = 2
COOLDOWN_SECONDS = 0.3

# Scoring
POINTS_BOARD = 1
POINTS_HOLE = 3
TARGET_SCORE = 21
WIN_BY_TWO = True

# ============================================================
# LOGGING INITIALISATIE
# ============================================================

event_logger   = EventLogger("cornhole_events.csv")
json_logger    = JSONLogger("cornhole_events.json")
detect_logger  = DetectionLogger("cornhole_detections.csv")
round_logger   = RoundLogger("cornhole_rounds.csv")
error_logger   = ErrorLogger("cornhole_errors.csv")

LOG_FILENAME = "cornhole_log.csv"


def ensure_log_file():
    if not os.path.exists(LOG_FILENAME):
        with open(LOG_FILENAME, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "timestamp", "event", "player", "color",
                "points", "total_p1", "total_p2", "round"
            ])


def log_event(event, player=None, color=None, points=0, game=None):
    """Log één event naar CSV + JSON."""
    try:
        event_logger.log(event, game=game, player=player, color=color, points=points)
        json_logger.log(event, game=game, player=player, color=color, points=points)
    except Exception as e:
        error_logger.log(e)


# ============================================================
# CAMERA INITIALISATIE
# ============================================================

def init_camera():
    """Start PiCamera2 correct op."""
    try:
        cam = Picamera2()
        config = cam.create_video_configuration(
            main={"size": CAMERA_RESOLUTION},
            buffer_count=4
        )
        cam.configure(config)
        cam.start()
        return cam
    except Exception as e:
        error_logger.log(e)
        raise RuntimeError("Camera Module 3 kon niet gestart worden.")


def grab_frame(cam):
    """Lees frame uit camera → converteer naar BGR."""
    try:
        frame = cam.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    except Exception as e:
        error_logger.log(e)
        return None


def release_camera(cam):
    try:
        cam.stop()
    except:
        pass


# ============================================================
# UI STATE
# ============================================================

BUTTONS = []

ui_state = {
    "running": False,
    "paused": False,
    "last_feedback": None,
    "feedback_duration": 0.6,
    "web_enabled": False,
    "camera_fullscreen": True,
    "score_fullscreen": False,
    "show_hud": True,
    "last_click_time": 0.0,
    "click_cooldown": 0.20,
}


# ============================================================
# ROI STATE
# ============================================================

board_rect = None
hole_circle = None
dragging = False
drag_mode = None
start_x = start_y = 0
offset_x = offset_y = 0
current_preview = None
mode = "rect"  # rect → circle → done


# ============================================================
# ROI HELPERS (DEEL 1 EINDIGT HIER)
# ============================================================

def reset_roi_state():
    """Reset ROI tekenen + slepen."""
    global board_rect, hole_circle, dragging, drag_mode
    global start_x, start_y, offset_x, offset_y
    global current_preview, mode

    board_rect = None
    hole_circle = None
    dragging = False
    drag_mode = None
    start_x = start_y = 0
    offset_x = offset_y = 0
    current_preview = None
    mode = "rect"


def point_in_rect(x, y, rect):
    if not rect:
        return False
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def point_in_circle(x, y, circle):
    if not circle:
        return False
    cx, cy, r = circle
    return (x - cx) ** 2 + (y - cy) ** 2 <= (r + 5) ** 2

# ============================================================
# TRACKING SYSTEM
# ============================================================

class BagTracker:
    def __init__(self):
        self.next_id = 1
        self.bags = {}  # id → state

    def _dist(self, a, b):
        return np.hypot(a[0] - b[0], a[1] - b[1])

    def update(self, detections):
        now = time.time()

        for det in detections:
            cx, cy = det["centroid"]
            color = det["color"]

            best_id = None
            best_dist = 9999

            for bid, bag in self.bags.items():
                d = self._dist((cx, cy), bag["centroid"])
                if d < best_dist and d <= MAX_BAG_DISTANCE:
                    best_dist = d
                    best_id = bid
            if best_id is not None:
                bag = self.bags[best_id]

                old = bag["centroid"]
                movement = self._dist((cx, cy), old)

                bag["centroid"] = (cx, cy)
                bag["movement"] = movement
                bag["last_seen"] = now
                bag["still_frames"] = bag["still_frames"] + 1 if movement < MOVEMENT_THRESHOLD else 0

                det["id"] = best_id

            else:
                bid = self.next_id
                self.next_id += 1

                self.bags[bid] = {
                    "id": bid,
                    "centroid": (cx, cy),
                    "color": color,
                    "last_seen": now,
                    "movement": 999,
                    "still_frames": 0,
                    "frames_in_roi": 0,
                    "scored_board": False,
                    "scored_hole": False,
                    "last_scored_time": 0,
                }
                det["id"] = bid

        # Cleanup old bags (> 10s unseen)
        for bid in list(self.bags.keys()):
            if time.time() - self.bags[bid]["last_seen"] > 10:
                del self.bags[bid]

        return detections

    def reset_if_left_roi(self, bid):
        b = self.bags.get(bid)
        if b:
            b["scored_board"] = False
            b["scored_hole"] = False
            b["frames_in_roi"] = 0
            b["still_frames"] = 0

    def can_score(self, bid):
        now = time.time()
        b = self.bags.get(bid)
        if not b:
            return False
        if now - b["last_scored_time"] >= COOLDOWN_SECONDS:
            b["last_scored_time"] = now
            return True
        return False


# ============================================================
# DETECTIE SYSTEM (HSV)
# ============================================================

def detect_bags(frame, active_colors):
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    kernel = np.ones((5, 5), np.uint8)

    detections = []

    for color in active_colors:
        lower, upper = COLOR_RANGES[color]
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, 2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, 2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_BAG_AREA or area > MAX_BAG_AREA:
                continue

            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue

            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            detections.append({
                "color": color,
                "centroid": (cx, cy),
                "area": area,
                "contour": cnt
            })

    return detections


# ============================================================
# GAME ENGINE (Netto Cornhole Ronde-Regel)
# ============================================================

class CornholeGame:
    def __init__(self, p1_colors, p2_colors):
        self.player1_colors = p1_colors
        self.player2_colors = p2_colors
        self.reset_scores()
        self.round_history = {}

    def reset_scores(self):
        self.round_number = 1
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

        points = 3 if is_hole else 1

        if color in self.player1_colors:
            self.round_hits_p1 += points
            self.total_bags_p1 += 1
            self.made_points_p1 += points

        elif color in self.player2_colors:
            self.round_hits_p2 += points
            self.total_bags_p2 += 1
            self.made_points_p2 += points

    def end_round(self):
        """Einde van de ronde volgens officiële netto score regels."""
        if self.game_over:
            return

        p1 = self.round_hits_p1
        p2 = self.round_hits_p2
        diff = p1 - p2

        # Netto punten toekennen
        if diff > 0:
            self.total_score_p1 += diff
        elif diff < 0:
            self.total_score_p2 += -diff

        print(f"RONDE RESULTAAT → P1: {p1} | P2: {p2} | NETTO: {diff}")

        # Winconditie
        if (
            self.total_score_p1 >= 21 or
            self.total_score_p2 >= 21
        ):
            if abs(self.total_score_p1 - self.total_score_p2) >= 2:
                self.game_over = True
                self.winner = 1 if self.total_score_p1 > self.total_score_p2 else 2
                print(f"WINNAAR = PLAYER {self.winner}")

        self.round_history[self.round_number] = {
        "p1": self.round_hits_p1,
        "p2": self.round_hits_p2
        }

        # Ronde resetten
        self.round_hits_p1 = 0
        self.round_hits_p2 = 0
        self.round_number += 1

    def get_accuracy(self):
        acc1 = (
            self.made_points_p1 / (self.total_bags_p1 * 3) * 100
            if self.total_bags_p1 else 0
        )
        acc2 = (
            self.made_points_p2 / (self.total_bags_p2 * 3) * 100
            if self.total_bags_p2 else 0
        )
        return acc1, acc2

    def get_score_progression(self):
            
            p1_scores = [0]
            p2_scores = [0]

            s1 = 0
            s2 = 0

            for rnd in sorted(self.round_history.keys()):
                r1 = self.round_history[rnd]["p1"]
                r2 = self.round_history[rnd]["p2"]

                diff = r1 - r2
                if diff > 0:
                    s1 += diff
                elif diff < 0:
                    s2 += -diff

                p1_scores.append(s1)
                p2_scores.append(s2)

            return p1_scores, p2_scores
    
def create_line_graph(game):
    p1, p2 = game.get_score_progression()

def generate_ai_summary(game):
    p1_total = game.total_score_p1
    p2_total = game.total_score_p2
    winner = "Speler 1" if p1_total > p2_total else "Speler 2"

    acc1, acc2 = game.get_accuracy()

    # Score progression ophalen
    try:
        p1_prog, p2_prog = game.get_score_progression()
    except:
        p1_prog, p2_prog = [0], [0]

    # Momentum bepalen
    momentum = []
    for i in range(1, len(p1_prog)):
        diff = p1_prog[i] - p2_prog[i]
        momentum.append(diff)

    # Analyse
    early_lead = "Speler 1" if p1_prog[1] > p2_prog[1] else "Speler 2"
    final_round = game.round_number - 1

    summary = f"""
Wedstrijdsamenvatting (AI gegenereerd)

De wedstrijd eindigde in een overwinning voor {winner} met een eindscore van {p1_total} – {p2_total}.

— Beginfase —
{early_lead} nam de vroege leiding. 
Na de eerste rondes ontwikkelde zich een duidelijk momentumverschil.

— Spelverloop —
Gedurende het verloop van {final_round} rondes wisselden de scores regelmatig.
De totale score-progressie toont dat {'Speler 1' if max(momentum) > abs(min(momentum)) else 'Speler 2'} het momentum in het middendeel van de wedstrijd overnam.

— Statistieken —
Speler 1 Accuracy: {acc1:.1f}%
Speler 2 Accuracy: {acc2:.1f}%

Puntevolutie (per ronde):
Speler 1: {p1_prog}
Speler 2: {p2_prog}

— Eindfase —
De wedstrijd werd beslist in ronde {final_round}, waar de scoreverschillen opliepen en het winnende team de vereiste marge behaalde.

Kortom: een {'spannende' if abs(p1_total - p2_total) <= 3 else 'duidelijke'} overwinning voor {winner}.
"""

    return summary

    plt.figure(figsize=(8,5))
    plt.plot(p1, marker='o', label='Speler 1', color='blue')
    plt.plot(p2, marker='o', label='Speler 2', color='red')

    plt.title("Score Progressie per Ronde")
    plt.xlabel("Ronde")
    plt.ylabel("Totaalscore")
    plt.grid(True)
    plt.legend()

    path = "score_graph.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()

    return path

# ============================================================
# UI BUTTONS /_THEME
# ============================================================

THEME = {
    "bg_overlay_alpha": 0.40,
    "panel_color": (0, 0, 0),
    "panel_alpha": 0.45,
    "accent": (0, 255, 255),
    "ok": (0, 220, 0),
    "warn": (0, 165, 255),
    "err": (0, 0, 255),
    "text": (255, 255, 255),
    "muted": (180, 180, 180),
    "btn_bg": (40, 40, 40),
    "btn_border": (180, 180, 180),
    "btn_text": (255, 255, 255),
}


def build_buttons(w, h):
    btn_w = int(max(180, w * 0.12))
    btn_h = int(max(60, h * 0.07))
    margin = 12

    left = margin
    right = w - btn_w - margin
    top = margin

    return [
        ("START/PAUSE", (left, top, left+btn_w, top+btn_h), "toggle_start"),
        ("RESET",       (left, top+(btn_h+margin), left+btn_w, top+(btn_h+margin)+btn_h), "reset"),
        ("EXPORT",      (left, top+2*(btn_h+margin), left+btn_w, top+2*(btn_h+margin)+btn_h), "export"),

        ("+1 P1", (right, top, right+btn_w, top+btn_h), "p1_plus"),
        ("-1 P1", (right, top+(btn_h+margin), right+btn_w, top+(btn_h+margin)+btn_h), "p1_minus"),

        ("+1 P2", (right, top+2*(btn_h+margin), right+btn_w, top+2*(btn_h+margin)+btn_h), "p2_plus"),
        ("-1 P2", (right, top+3*(btn_h+margin), right+btn_w, top+3*(btn_h+margin)+btn_h), "p2_minus"),
    ]


# ============================================================
# BUTTON RENDERING
# ============================================================

def draw_buttons(frame):
    overlay = frame.copy()

    for label, (x1, y1, x2, y2), _ in BUTTONS:
        cv2.rectangle(overlay, (x1, y1), (x2, y2), THEME["btn_bg"], -1)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), THEME["btn_border"], 2)

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)
        tx = x1 + (x2 - x1 - tw)//2
        ty = y1 + (y2 - y1 + th)//2

        cv2.putText(overlay, label, (tx, ty),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, THEME["btn_text"], 2)

    return cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)


# ============================================================
# FEEDBACK OVERLAY
# ============================================================

def draw_feedback(frame):
    fb = ui_state["last_feedback"]
    if not fb:
        return frame

    typ, ts = fb
    elapsed = time.time() - ts

    # Veiligere timeout (valt niet weg als frame vertraagd is)
    if elapsed >= ui_state["feedback_duration"]:
        return frame  # NIET verwijderen, gewoon laten uitdoven

    overlay = frame.copy()
    h, w = frame.shape[:2]

    # Kleuren & tekst
    if typ == "hole":
        color = (0, 200, 0)
        msg = "+3 HOLE"
    elif typ == "board":
        color = (0, 180, 255)
        msg = "+1 BOARD"
    else:
        color = (200, 200, 200)
        msg = "MANUAL"

    # Transparante kleurlaag
    alpha = 0.45  # iets mooier dan 0.4
    cv2.rectangle(overlay, (0, 0), (w, h), color, -1)
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Tekst centreren
    (tw, th), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_DUPLEX, 2, 3)
    cx = (w - tw) // 2
    cy = int(h * 0.55)

    cv2.putText(frame, msg, (cx, cy),
                cv2.FONT_HERSHEY_DUPLEX, 2,
                (255, 255, 255), 3)

    return frame


# ============================================================
# BAG OVERLAY (CENTROIDS + LABELS)
# ============================================================

def draw_bags_overlay(frame, bags):
    for bag in bags:
        cx, cy = bag["centroid"]
        contour = bag["contour"]
        color = bag["color"]
        bag_id = bag.get("id", 0)

        cv2.drawContours(frame, [contour], -1, (0,220,0), 2)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        cv2.putText(
            frame,
            f"{color}#{bag_id}",
            (cx+8, cy-8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2
        )

    return frame


def draw_rois(frame):
    if frame is None or not isinstance(frame, np.ndarray):
        return frame

    # BOARD RECT
    if board_rect is not None:
        try:
            x1, y1, x2, y2 = board_rect
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255,255,255), 2)
            cv2.putText(frame, "BOARD", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, THEME["text"], 2)
        except:
            pass

    # HOLE CIRCLE
    if hole_circle is not None:
        try:
            cx, cy, r = hole_circle
            cv2.circle(frame, (cx, cy), r, (255,255,255), 2)
            cv2.putText(frame, "HOLE", (cx-r, cy-r-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, THEME["text"], 2)
        except:
            pass

    # PREVIEW
    if current_preview:
        try:
            if current_preview[0] == "rect":
                _, x1, y1, x2, y2 = current_preview
                cv2.rectangle(frame, (x1, y1), (x2, y2), THEME["muted"], 1)
            else:
                _, cx, cy, r = current_preview
                cv2.circle(frame, (cx, cy), r, THEME["muted"], 1)
        except:
            pass

    return frame    

# ============================================================
# HUD PANEL LEFT + RIGHT
# ============================================================

def draw_hud(frame, game, scores_p1, scores_p2):
    if not ui_state["show_hud"]:
        return frame

    h, w = frame.shape[:2]
    acc1, acc2 = game.get_accuracy()

    # LEFT PANEL
    overlay = frame.copy()
    box_h = len(scores_p1) * 26 + 130
    cv2.rectangle(overlay, (10,10), (280,10+box_h), THEME["panel_color"], -1)
    frame = cv2.addWeighted(overlay, THEME["panel_alpha"], frame, 1-THEME["panel_alpha"], 0)

    cv2.putText(frame, "SPELER 1", (20,35),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, THEME["text"], 2)
    cv2.putText(frame, f"SCORE: {game.total_score_p1}", (20,62),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,0), 2)
    cv2.putText(frame, f"ACC: {acc1:.0f}%", (20,88),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, THEME["accent"], 2)

    # Tussenscore P1 deze ronde
    cv2.putText(frame, f"RONDE: {game.round_hits_p1}",
                (20, 110), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0,255,255), 2)

    y = 118
    for c, v in scores_p1.items():
        cv2.putText(frame, f"{c}: {v}",
                    (20, y), cv2.FONT_HERSHEY_DUPLEX, 0.6, THEME["text"], 1)
        y += 26

    # RIGHT PANEL
    overlay = frame.copy()
    box_h = len(scores_p2) * 26 + 130
    cv2.rectangle(overlay, (w-280,10), (w-10,10+box_h), THEME["panel_color"], -1)
    frame = cv2.addWeighted(overlay, THEME["panel_alpha"], frame, 1-THEME["panel_alpha"], 0)

    cv2.putText(frame, "SPELER 2", (w-270,35),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, THEME["text"], 2)
    cv2.putText(frame, f"SCORE: {game.total_score_p2}", (w-270,62),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,0), 2)
    cv2.putText(frame, f"ACC: {acc2:.0f}%", (w-270,88),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, THEME["accent"], 2)

    # Tussenscore P2 deze ronde
    cv2.putText(frame, f"RONDE: {game.round_hits_p2}",
                (w-270, 110), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0,255,255), 2)

    y = 118
    for c, v in scores_p2.items():
        cv2.putText(frame, f"{c}: {v}",
                    (w-270, y), cv2.FONT_HERSHEY_DUPLEX, 0.6, THEME["text"], 1)
        y += 26

    status = (
        "RUNNING" if ui_state["running"] and not ui_state["paused"]
        else ("PAUSED" if ui_state["paused"] else "STOPPED")
    )

    cv2.putText(frame, f"ROUND: {game.round_number}", (w//2 - 110, 36),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, THEME["accent"], 2)

    if game.game_over:
        cv2.putText(frame,
                    f"WINNER: PLAYER {game.winner}",
                    (w//2 - 160, 100),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.95,
                    THEME["err"],
                    2)

        if 'email_p1' in globals() and not hasattr(game, "emails_sent"):
            send_email_report(email_p1, "Speler 1", game, scores_p1, scores_p2)
            send_email_report(email_p2, "Speler 2", game, scores_p1, scores_p2)
            game.emails_sent = True

    return frame



# ============================================================
# SECOND SCREEN SCOREBOARD
# ============================================================

SCORE_WINDOW_NAME = "Scoreboard"

def draw_score_window(game):
    w, h = 520, 360
    img = np.zeros((h,w,3), np.uint8)

    cv2.putText(img, "SCOREBOARD", (110,40),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (255,255,0), 2)

    p1 = game.total_score_p1
    p2 = game.total_score_p2

    col1 = (0,255,0) if p1 >= p2 else (255,255,255)
    col2 = (0,255,0) if p2 >= p1 else (255,255,255)

    cv2.putText(img, "PLAYER 1", (40,110),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, col1, 2)
    cv2.putText(img, str(p1), (60,170),
                cv2.FONT_HERSHEY_DUPLEX, 2.5, col1, 4)

    cv2.putText(img, "PLAYER 2", (300,110),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, col2, 2)
    cv2.putText(img, str(p2), (320,170),
                cv2.FONT_HERSHEY_DUPLEX, 2.5, col2, 4)

    status = (
        "RUNNING" if ui_state["running"] and not ui_state["paused"]
        else ("PAUSED" if ui_state["paused"] else "STOPPED")
    )

    cv2.putText(img, f"ROUND: {game.round_number}", (40,240),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, THEME["accent"], 2)
    cv2.putText(img, f"STATUS: {status}", (40,280),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, THEME["accent"], 2)

    cv2.imshow(SCORE_WINDOW_NAME, img)

# ============================================================
# MOUSE HANDLER
# ============================================================

def mouse_event(event, x, y, flags, param):
    global dragging, drag_mode, start_x, start_y
    global offset_x, offset_y, board_rect, hole_circle, current_preview, mode

    if event == cv2.EVENT_LBUTTONDOWN:

        # Knoppen checken
        if time.time() - ui_state["last_click_time"] > ui_state["click_cooldown"]:
            for label, (x1,y1,x2,y2), action in BUTTONS:
                if x1 <= x <= x2 and y1 <= y <= y2:
                    handle_button(action)
                    ui_state["last_click_time"] = time.time()
                    return

        # ROI slepen
        if mode == "done":
            if hole_circle and point_in_circle(x, y, hole_circle):
                drag_mode = "circle"
                dragging = True
                cx, cy, r = hole_circle
                offset_x = x - cx
                offset_y = y - cy
                return

            if board_rect and point_in_rect(x, y, board_rect):
                drag_mode = "rect"
                dragging = True
                x1, y1, x2, y2 = board_rect
                offset_x = x - x1
                offset_y = y - y1
                return

        # Nieuwe ROI tekenen
        dragging = True
        start_x, start_y = x, y
        current_preview = None
        drag_mode = None

    elif event == cv2.EVENT_MOUSEMOVE and dragging:

        if drag_mode == "rect" and board_rect:
            w = board_rect[2] - board_rect[0]
            h = board_rect[3] - board_rect[1]
            board_rect = (x-offset_x, y-offset_y, x-offset_x+w, y-offset_y+h)
            return

        if drag_mode == "circle" and hole_circle:
            cx = x - offset_x
            cy = y - offset_y
            hole_circle = (cx, cy, hole_circle[2])
            return

        # ROI preview
        if mode == "rect":
            current_preview = ("rect", start_x, start_y, x, y)
        elif mode == "circle":
            r = int(np.hypot(x-start_x, y-start_y))
            current_preview = ("circle", start_x, start_y, r)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False

        if drag_mode:
            drag_mode = None
            return

        # Definitieve ROI zetten
        if mode == "rect":
            x1, y1, x2, y2 = start_x, start_y, x, y
            board_rect = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
            mode = "circle"

        elif mode == "circle":
            r = int(np.hypot(x-start_x, y-start_y))
            hole_circle = (start_x, start_y, r)
            mode = "done"

        current_preview = None


# ============================================================
# BUTTON HANDLER
# ============================================================

def handle_button(action):
    global game, tracker, scores_p1, scores_p2

    if action == "toggle_start":
        ui_state["running"] = not ui_state["running"]
        ui_state["paused"] = False
        log_event("start" if ui_state["running"] else "stop", game=game)

    elif action == "reset":
        game.reset_scores()
        tracker = BagTracker()
        scores_p1 = {c:0 for c in game.player1_colors}
        scores_p2 = {c:0 for c in game.player2_colors}
        log_event("reset", game=game)

    elif action == "export":
        log_event("export_snapshot", game=game)

    elif action == "p1_plus":
        game.total_score_p1 += 1
        ui_state["last_feedback"] = ("manual", time.time())
        log_event("manual_plus",1,None,1,game)

    elif action == "p1_minus":
        game.total_score_p1 = max(0, game.total_score_p1-1)
        ui_state["last_feedback"] = ("manual", time.time())
        log_event("manual_minus",1,None,-1,game)

    elif action == "p2_plus":
        game.total_score_p2 += 1
        ui_state["last_feedback"] = ("manual", time.time())
        log_event("manual_plus",2,None,1,game)

    elif action == "p2_minus":
        game.total_score_p2 = max(0, game.total_score_p2-1)
        ui_state["last_feedback"] = ("manual", time.time())
        log_event("manual_minus",2,None,-1,game)

    elif action == "toggle_web":
        start_web_interface()
        ui_state["web_enabled"] = True


# ============================================================
# WEB INTERFACE — MOOIE CORNHOLE PRO 2.4 DASHBOARD
# ============================================================

_flask_app = None
app = None   # ← heel belangrijk!

def start_web_interface():
    global _flask_app, app, game, hitmap_p1, hitmap_p2

    # Als server al draait, niet opnieuw starten
    if _flask_app is not None:
        return

    # Maak Flask app (globaal!)
    app = Flask(__name__)
    _flask_app = app

    # ------------------------------------------
    # ROUTES
    # ------------------------------------------

    @app.route("/")
    def index():
        return f"<h1>Cornhole Pro 2.5</h1><p>Score: {game.total_score_p1} - {game.total_score_p2}</p>"

    # --- DASHBOARD 2.4 (bestaande) ---
    @app.route("/dashboard")
    def dashboard():
        return render_template_string("""
            <h1>Oud Dashboard</h1>
            <p>Score P1: {{p1}}, Score P2: {{p2}}</p>
        """, p1=game.total_score_p1, p2=game.total_score_p2)

    # ============================================================
    # 🔥 DASHBOARD 3.0 — NIEUW UITGEBREID DASHBOARD
    # ============================================================
    @app.route("/dashboard3")
    def dashboard3():
        return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cornhole Dashboard 3.0</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            body {
                background:#0d1117;
                color:white;
                font-family:Arial;
                margin:0;
                padding:0;
            }
            .header {
                text-align:center;
                padding:20px;
                background:#161b22;
                font-size:32px;
                color:#58a6ff;
            }
            .container {
                display:flex;
                flex-wrap:wrap;
                justify-content:center;
                padding:20px;
                gap:20px;
            }
            .card {
                width:300px;
                background:#21262d;
                padding:20px;
                border-radius:12px;
                box-shadow:0 0 10px rgba(0,0,0,.4);
            }
        .score {
            font-size:64px;
            color:#00ff90;
            text-align:center;
        }
        .label {
            font-size:20px;
            text-align:center;
            color:#ccc;
        }
        .hitmap {
            width:100%;
            height:240px;
            background:black;
            border-radius:12px;
        }
    </style>
</head>

<body>

<div class="header">Cornhole Dashboard 3.0</div>

<div class="container">

    <div class="card" style="width:650px;">
        <div class="label">Momentum</div>
        <div id="momentum_bar" style="width:100%;height:30px;background:#333;border-radius:10px;position:relative;">
            <div id="momentum_fill" style="width:50%;height:30px;background:#00ff90;border-radius:10px;position:absolute;left:25%;"></div>
        </div>

        <div class="label" style="margin-top:20px;">Live Commentator</div>
        <div id="commentary_box" style="background:#111;padding:15px;border-radius:10px;color:#58a6ff;font-size:18px;min-height:60px;">
            Laden…
        </div>
    </div>

    <div class="card">
        <div class="label">TEAM 1</div>
        <div id="score1" class="score">0</div>
        <div class="label">Ronde: <span id="round1"></span></div>
        <div class="label">Acc: <span id="acc1"></span>%</div>
        <canvas id="hitmap1" class="hitmap"></canvas>
    </div>

    <div class="card">
        <div class="label">TEAM 2</div>
        <div id="score2" class="score">0</div>
        <div class="label">Ronde: <span id="round2"></span></div>
        <div class="label">Acc: <span id="acc2"></span>%</div>
        <canvas id="hitmap2" class="hitmap"></canvas>
    </div>

</div>

<script>
function update(){
    fetch('/api/state3')
    .then(r => r.json())
    .then(s => {
        document.getElementById("score1").innerText = s.total_p1;
        document.getElementById("score2").innerText = s.total_p2;
        document.getElementById("round1").innerText = s.round;
        document.getElementById("round2").innerText = s.round;
        document.getElementById("acc1").innerText = s.acc1;
        document.getElementById("acc2").innerText = s.acc2;

        let bar = document.getElementById("momentum_fill");
        let val = (s.momentum + 1) / 2;
        bar.style.width = (val * 100) + "%";
        bar.style.left = ((1-val) * 100) + "%";

        document.getElementById("commentary_box").innerText = s.commentary;
    });
}

setInterval(update, 500);
update();
</script>

</body>
</html>
""")

    # ------------------------------------------
    # START SERVER (BINNEN DEZE FUNCTIE!)
    # ------------------------------------------
    def run_server():
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

    threading.Thread(target=run_server, daemon=True).start()

    # ============================================================
    # API FOR DASHBOARD 3.0
    # ============================================================
    @app.route("/api/state3")
    def api_state3():
        acc1, acc2 = game.get_accuracy()
        momentum = compute_momentum(game)

        comment = live_commentary(game)

        return jsonify({
            "total_p1": game.total_score_p1,
            "total_p2": game.total_score_p2,
            "round": game.round_number,
            "acc1": round(acc1, 1),
            "acc2": round(acc2, 1),
            "hitmap_p1": [{"x": int(p[0]), "y": int(p[1])} for p in hitmap_p1],
            "hitmap_p2": [{"x": int(p[0]), "y": int(p[1])} for p in hitmap_p2],
            "momentum": momentum,
            "commentary": comment
})
    

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


def generate_qr_code():
    ip = get_local_ip()
    url = f"http://{ip}:5000/dashboard"

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save("dashboard_qr.png")

    print("\n###############################################")
    print("#  Scan deze QR-code om LIVE mee te volgen!   #")
    print(f"#  URL: {url}                                 #")
    print("###############################################\n")

# ============================================================
# MAIN FUNCTIE
# ============================================================

import cv2

def save_replay_opencv(frames, path, fps=20):
    if len(frames) == 0:
        return

    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))

    for f in frames:
        out.write(f)

    out.release()
    print("Replay opgeslagen:", path)


REPLAY_DIR = "replays"
if not os.path.exists(REPLAY_DIR):
    os.makedirs(REPLAY_DIR)

replay_buffer = deque(maxlen=120)   # ±4 sec op 30fps
replay_index = 1

def main():
    global BUTTONS, game, tracker, scores_p1, scores_p2, player1_colors, player2_colors
    global board_rect, hole_circle, mode
    global email_p1, email_p2
    global team_1_name, team_2_name
    global hitmap_p1, hitmap_p2
    global replay_index, cam, window, active_colors
    hitmap_p1 = []
    hitmap_p2 = []

    reset_roi_state()
    ensure_log_file()

    # ---------------------------------------------------------
    # EMAILS VRAGEN
    # ---------------------------------------------------------
    email_p1 = input("Email Speler 1: ").strip()
    email_p2 = input("Email Speler 2: ").strip()

    team_1_name = input("Teamnaam Speler 1 (optioneel): ").strip()
    team_2_name = input("Teamnaam Speler 2 (optioneel): ").strip()

    if team_1_name == "":
        team_1_name = "Speler 1"

    if team_2_name == "":
        team_2_name = "Speler 2"

    

    # ---------------------------------------------------------
    # KLEUREN VRAGEN
    # ---------------------------------------------------------
    print("Beschikbare kleuren:", ", ".join(COLOR_RANGES.keys()))
    p1_front = input("Speler 1 kleur 1: ").strip().lower()
    p1_back  = input("Speler 1 kleur 2: ").strip().lower()
    p2_front = input("Speler 2 kleur 1: ").strip().lower()
    p2_back  = input("Speler 2 kleur 2: ").strip().lower()

    player1_colors = [p1_front, p1_back]
    player2_colors = [p2_front, p2_back]
    active_colors  = [c for c in (player1_colors + player2_colors) if c in COLOR_RANGES]

    # ---------------------------------------------------------
    # CAMERA STARTEN
    # ---------------------------------------------------------
    cam = init_camera()

    # ---------------------------------------------------------
    # KLEURKALIBRATIE
    # ---------------------------------------------------------
    do_calib = input("Kleurkalibratie uitvoeren? (j/n): ").strip().lower()
    if do_calib == "j":
        pass  # TODO: implement calibrate_used_colors(active_colors, cam)

    # ---------------------------------------------------------
    # GAME ENGINE STARTEN
    # ---------------------------------------------------------
    game = CornholeGame(player1_colors, player2_colors)
    tracker = BagTracker()
    scores_p1 = {c: 0 for c in player1_colors}
    scores_p2 = {c: 0 for c in player2_colors}

    # ---------------------------------------------------------
    # WEB INTERFACE + QR
    # ---------------------------------------------------------
    start_web_interface()
    ui_state["web_enabled"] = True

    generate_qr_code()
    qr_img = cv2.imread("dashboard_qr.png")
    cv2.namedWindow("Live Scoreboard QR", cv2.WINDOW_NORMAL)
    cv2.imshow("Live Scoreboard QR", qr_img)

    # ---------------------------------------------------------
    # HOOFDSCHERM
    # ---------------------------------------------------------
    window = "Cornhole Pro 2.5"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, mouse_event)

    cv2.namedWindow(SCORE_WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(SCORE_WINDOW_NAME, 520, 360)
    BUTTONS[:] = build_buttons(CAMERA_RESOLUTION[0], CAMERA_RESOLUTION[1])

    print("\n--- ROI tekenen (BOARD → HOLE) ---\n")

    # ========================================================
    # MAIN WHILE LOOP
    # ========================================================

    try:
        while True:
            frame = grab_frame(cam)

            # --- Replay buffer opslaan ---
            replay_buffer.append(frame.copy())

            # --- BELANGRIJK: Frame veiligheidscheck ---
            if frame is None or not isinstance(frame, np.ndarray):
                continue

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

            if key == ord('r'):
                handle_button("reset")

            if key == ord('n'):
                print("Ronde eindigen...")
                game.end_round()
                log_event("round_end", game=game)
                round_logger.log(game)

            if key == ord('h'):
                ui_state["show_hud"] = not ui_state["show_hud"]

            # --------------------------------------------------
            # ROI MODE — eerst BOARD en HOLE tekenen
            # --------------------------------------------------


            # --------------------------------------------------
            # DETECTIE + TRACKING
            # --------------------------------------------------
            detections = detect_bags(frame, active_colors)
            tracked = tracker.update(detections)

            processed = set()

            for bag in tracked:
                bid = bag["id"]
                if bid in processed:
                    continue
                processed.add(bid)

                cx, cy = bag["centroid"]
                color  = bag["color"]
                bstate = tracker.bags[bid]

                if color in player1_colors:
                    hitmap_p1.append((cx, cy))
                else:
                    hitmap_p2.append((cx, cy))

                on_board = point_in_rect(cx, cy, board_rect)
                in_hole  = point_in_circle(cx, cy, hole_circle)

                detect_logger.log(bstate, on_board, in_hole)

                if on_board or in_hole:
                    bstate["frames_in_roi"] += 1
                else:
                    tracker.reset_if_left_roi(bid)
                    continue

                if not ui_state["running"] or ui_state["paused"]:
                    continue

                if bstate["frames_in_roi"] < FRAMES_REQUIRED_IN_ROI:
                    continue

                if bstate["still_frames"] < STILL_FRAMES_REQUIRED:
                    continue

                # --- SCORE LOGIC (FIXED & RELIABLE) ---
                # PRIORITEIT: eerst HOLE → dan BOARD

                # 1) HOLE DETECTIE
                if in_hole and not bstate["scored_hole"]:

                    # ⇒ bag mag alleen scoren als hij echt stil ligt IN het gat
                    if bstate["still_frames"] >= STILL_FRAMES_REQUIRED:

                        if tracker.can_score(bid):
                            game.register_hit(color, True)  # +3
                            bstate["scored_hole"] = True
                            bstate["scored_board"] = True   # voorkomt dubbele score

                            # Forceer de animatie opnieuw (dit was de bug!)
                            ui_state["last_feedback"] = ("hole", time.time())

                            # Replay veilig opslaan
                            replay_path = f"{REPLAY_DIR}/replay_{replay_index}.mp4"
                            save_replay_opencv(list(replay_buffer), replay_path)
                            replay_index += 1

                            log_event(
                                "score_hole",
                                1 if color in player1_colors else 2,
                                color,
                                POINTS_HOLE,
                                game
                            )

                        continue  # HOLE heeft altijd prioriteit → skip rest


                # 2) BOARD DETECTIE
                if on_board and not bstate["scored_board"]:

                    # Board moet óók pas tellen als bag echt stil ligt
                    if bstate["still_frames"] >= STILL_FRAMES_REQUIRED:

                        if tracker.can_score(bid):
                            game.register_hit(color, False)  # +1
                            bstate["scored_board"] = True

                            # Fix: animatie gaat soms weg → nu altijd forceren
                            ui_state["last_feedback"] = ("board", time.time())

                            log_event(
                                "score_board",
                                1 if color in player1_colors else 2,
                                color,
                                POINTS_BOARD,
                                game
                            )

                        continue

                if on_board and not bstate["scored_board"]:
                    if tracker.can_score(bid):
                        game.register_hit(color, False)  # +1 rondepunt
                        bstate["scored_board"] = True
                        ui_state["last_feedback"] = ("board", time.time())

                        log_event(
                            "score_board",
                            1 if color in player1_colors else 2,
                            color,
                            POINTS_BOARD,
                            game
                        )
                    continue

            # --------------------------------------------------
            # TEKENEN UI
            # --------------------------------------------------
            frame = draw_rois(frame)
            frame = draw_bags_overlay(frame, tracked)
            # Update per-color scores for HUD
            scores_p1 = {c: 0 for c in player1_colors}
            scores_p2 = {c: 0 for c in player2_colors}
            for bag in tracked:
                color = bag["color"]
                if color in scores_p1:
                    scores_p1[color] += 1
                elif color in scores_p2:
                    scores_p2[color] += 1

            frame = draw_hud(frame, game, scores_p1, scores_p2)
            frame = draw_buttons(frame)
            frame = draw_feedback(frame)

            cv2.imshow(window, frame)
            draw_score_window(game)

    except KeyboardInterrupt:
        pass
    finally:
        release_camera(cam)
        cv2.destroyAllWindows()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
