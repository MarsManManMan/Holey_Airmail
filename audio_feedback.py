# audio_feedback.py
import threading
from config import AUDIO_ENABLED

try:
    import pygame
    pygame.mixer.init()
    SOUND_ENABLED = True
except Exception:
    SOUND_ENABLED = False

SOUNDS = {}

def load_sounds():
    if not AUDIO_ENABLED or not SOUND_ENABLED:
        return
    # Zet hier pad naar je wav/ogg bestanden
    try:
        SOUNDS["point1"] = pygame.mixer.Sound("point1.wav")
        SOUNDS["point3"] = pygame.mixer.Sound("point3.wav")
        SOUNDS["round_end"] = pygame.mixer.Sound("round_end.wav")
        SOUNDS["win"] = pygame.mixer.Sound("win.wav")
    except Exception:
        pass


def _play(name):
    if not AUDIO_ENABLED or not SOUND_ENABLED:
        return
    s = SOUNDS.get(name)
    if s:
        s.play()


def play_point(points):
    if points == 3:
        threading.Thread(target=_play, args=("point3",), daemon=True).start()
    elif points == 1:
        threading.Thread(target=_play, args=("point1",), daemon=True).start()


def play_round_end():
    threading.Thread(target=_play, args=("round_end",), daemon=True).start()


def play_win():
    threading.Thread(target=_play, args=("win",), daemon=True).start()
