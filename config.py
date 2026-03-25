# config.py

CAMERA_RESOLUTION = (640, 480)

COLOR_RANGES = {
    "blauw": [(90, 50, 50), (130, 255, 255)],
    "groen": [(35, 40, 40), (90, 255, 255)],
    "geel":  [(20, 70, 70), (35, 255, 255)],
    "zwart": [(0, 0, 0), (180, 255, 40)],
    "rood":  [(0, 120, 70), (10, 255, 255)],
    "wit":   [(0, 0, 200), (180, 40, 255)],
    "roze":  [(140, 50, 50), (175, 255, 255)],
}

MIN_BAG_AREA = 1500          # contour area
COOLDOWN_SECONDS = 0.5       # per bag ID, niet per kleur
MAX_BAG_DISTANCE = 60        # max pixelafstand om dezelfde bag te tracken

POINTS_BOARD = 1
POINTS_HOLE = 3

TARGET_SCORE = 21            # Cornhole target
WIN_BY_TWO = True

AUDIO_ENABLED = True
WEB_SERVER_PORT = 8080
