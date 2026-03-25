# main.py
import cv2
import time
from picamera2 import Picamera2

from config import CAMERA_RESOLUTION, WEB_SERVER_PORT
from roi import mouse_event, draw_rois, reset_roi_state, board_rect, hole_circle, is_in_rect, is_in_circle, mode
from detection import detect_bags, BagTracker
from scoring import CornholeGame
from hud import draw_hud, draw_bags_overlay
from audio_feedback import load_sounds, play_point, play_round_end, play_win
from web_scoreboard import start_server, update_scoreboard

def main():
    reset_roi_state()

    print("Beschikbare kleuren zie config.py")
    p1_front = input("Speler 1 voor-kleur: ").strip().lower()
    p1_back  = input("Speler 1 achter-kleur: ").strip().lower()
    p2_front = input("Speler 2 voor-kleur: ").strip().lower()
    p2_back  = input("Speler 2 achter-kleur: ").strip().lower()

    player1_colors = [p1_front, p1_back]
    player2_colors = [p2_front, p2_back]
    active_colors = player1_colors + player2_colors

    # game engine
    game = CornholeGame(player1_colors, player2_colors)

    # scores per kleur (voor HUD)
    scores_p1 = {c: 0 for c in player1_colors}
    scores_p2 = {c: 0 for c in player2_colors}

    # tracker
    tracker = BagTracker()

    # audio
    load_sounds()

    # web scoreboard
    start_server(WEB_SERVER_PORT)
    print(f"Webscoreboard beschikbaar op poort {WEB_SERVER_PORT} (http://<raspberry-ip>:{WEB_SERVER_PORT})")

    # camera
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={"size": CAMERA_RESOLUTION},
        buffer_count=4
    )
    picam2.configure(config)
    picam2.start()

    cv2.namedWindow("Cornhole Pro", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Cornhole Pro", 1280, 960)
    cv2.setMouseCallback("Cornhole Pro", mouse_event)

    print("\n--- ROI configuratie ---")
    print("1) Teken een rechthoek rond het BOARD (1 punt).")
    print("2) Teken daarna een cirkel rond het HOLE (3 punten).")
    print("Daarna kun je ze verslepen.")
    print("Druk 'n' om een ronde handmatig te eindigen.")
    print("Druk 'r' om spel te resetten.")
    print("Druk 'q' om te stoppen.\n")

    try:
        while True:
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            if key == ord('r'):
                print("Reset game.")
                game.reset_scores()
                scores_p1 = {c: 0 for c in player1_colors}
                scores_p2 = {c: 0 for c in player2_colors}
            if key == ord('n'):
                print("Ronde eindigen.")
                game.end_round()
                play_round_end()
                if game.game_over:
                    play_win()
                update_scoreboard(game)

            # eerst ROI tekenen/config
            from roi import mode as roi_mode  # import actuele mode
            if roi_mode != "done":
                frame = draw_rois(frame)
                cv2.putText(frame, "Teken eerst BOARD & HOLE", (20, frame.shape[0] - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.imshow("Cornhole Pro", frame)
                continue

            # detectie
            raw_bags = detect_bags(frame, active_colors)
            tracked_bags = tracker.update(raw_bags)

            # scoring per bag
            for bag in tracked_bags:
                cx, cy = bag["centroid"]
                color = bag["color"]
                bid = bag["id"]

                on_board = is_in_rect(cx, cy, board_rect)
                in_hole = is_in_circle(cx, cy, hole_circle)

                if on_board or in_hole:
                    if tracker.can_score(bid):
                        points = 3 if in_hole else 1
                        # game engine
                        game.register_hit(color, is_hole=in_hole)
                        play_point(points)

                        # kleur-specifieke scores
                        if color in scores_p1:
                            scores_p1[color] += points
                        if color in scores_p2:
                            scores_p2[color] += points

                        update_scoreboard(game)

                        print(f"Score: kleur={color}, points={points}, total_p1={game.total_score_p1}, total_p2={game.total_score_p2}")

            # teken overlay
            frame = draw_rois(frame)
            frame = draw_bags_overlay(frame, tracked_bags)
            frame = draw_hud(frame, game, scores_p1, scores_p2)

            cv2.imshow("Cornhole Pro", frame)

    finally:
        cv2.destroyAllWindows()
        picam2.stop()


if __name__ == "__main__":
    main()
