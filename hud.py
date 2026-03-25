# hud.py
import cv2

def draw_hud(frame, game, scores_p1, scores_p2):
    h, w = frame.shape[:2]

    acc1, acc2 = game.get_accuracy()

    # HUD speler 1 links
    overlay = frame.copy()
    box_h = len(scores_p1) * 25 + 120
    cv2.rectangle(overlay, (10, 10), (260, 10 + box_h), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.45, frame, 0.55, 0)

    cv2.putText(frame, "SPELER 1", (20, 35),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"SCORE: {game.total_score_p1}", (20, 60),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"ACCURACY: {acc1:.0f}%", (20, 85),
                cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 2)

    y = 115
    for c, v in scores_p1.items():
        cv2.putText(frame, f"{c}: {v}", (20, y),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        y += 25

    # HUD speler 2 rechts
    overlay = frame.copy()
    box_h = len(scores_p2) * 25 + 120
    cv2.rectangle(overlay, (w - 260, 10), (w - 10, 10 + box_h), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.45, frame, 0.55, 0)

    cv2.putText(frame, "SPELER 2", (w - 240, 35),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"SCORE: {game.total_score_p2}", (w - 240, 60),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"ACCURACY: {acc2:.0f}%", (w - 240, 85),
                cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 255), 2)

    y = 115
    for c, v in scores_p2.items():
        cv2.putText(frame, f"{c}: {v}", (w - 240, y),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        y += 25

    # Ronde + game status bovenaan
    text = f"ROUND: {game.round_number}"
    cv2.putText(frame, text, (int(w / 2) - 80, 30),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 255), 2)

    if game.game_over:
        msg = f"WINNER: PLAYER {game.winner}"
        cv2.putText(frame, msg, (int(w / 2) - 140, 60),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 255), 2)

    return frame


def draw_bags_overlay(frame, bags):
    # bags: list met dicts {id, color, centroid, contour}
    for bag in bags:
        cx, cy = bag["centroid"]
        cnt = bag["contour"]
        color = bag["color"]
        bid = bag.get("id", 0)

        cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(frame, f"{color}#{bid}", (cx + 5, cy - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return frame
