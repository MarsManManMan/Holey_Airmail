# roi.py
import cv2
import numpy as np

board_rect = None   # (x1, y1, x2, y2)
hole_circle = None  # (cx, cy, r)

dragging = False
drag_mode = None    # "rect", "circle", None
start_x, start_y = 0, 0
offset_x, offset_y = 0, 0
current_preview = None
mode = "rect"       # "rect" -> "circle" -> "done"


def reset_roi_state():
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
    return (x - cx)**2 + (y - cy)**2 <= r*r


def mouse_event(event, x, y, flags, param):
    global dragging, drag_mode, start_x, start_y
    global board_rect, hole_circle, offset_x, offset_y
    global current_preview, mode

    if event == cv2.EVENT_LBUTTONDOWN:
        # Verslepen als klaar
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

        # Tekenen
        dragging = True
        drag_mode = None
        start_x, start_y = x, y
        current_preview = None

    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        if mode == "done" and drag_mode == "rect" and board_rect:
            w = board_rect[2] - board_rect[0]
            h = board_rect[3] - board_rect[1]
            board_rect = (x - offset_x, y - offset_y,
                          x - offset_x + w, y - offset_y + h)
            return

        if mode == "done" and drag_mode == "circle" and hole_circle:
            cx = x - offset_x
            cy = y - offset_y
            hole_circle = (cx, cy, hole_circle[2])
            return

        if mode == "rect":
            current_preview = ("rect", start_x, start_y, x, y)
        elif mode == "circle":
            radius = int(np.hypot(x - start_x, y - start_y))
            current_preview = ("circle", start_x, start_y, radius)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False

        if drag_mode:
            drag_mode = None
            return

        if mode == "rect":
            x1, y1, x2, y2 = start_x, start_y, x, y
            board_rect = (min(x1, x2), min(y1, y2),
                          max(x1, x2), max(y1, y2))
            mode = "circle"

        elif mode == "circle":
            radius = int(np.hypot(x - start_x, y - start_y))
            hole_circle = (start_x, start_y, radius)
            mode = "done"

        current_preview = None


def draw_rois(frame):
    if board_rect:
        x1, y1, x2, y2 = board_rect
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        cv2.putText(frame, "BOARD", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if hole_circle:
        cx, cy, r = hole_circle
        cv2.circle(frame, (cx, cy), r, (255, 255, 255), 2)
        cv2.putText(frame, "HOLE", (cx - r, cy - r - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if current_preview:
        if current_preview[0] == "rect":
            _, x1, y1, x2, y2 = current_preview
            cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), 1)
        else:
            _, cx, cy, r = current_preview
            cv2.circle(frame, (cx, cy), r, (200, 200, 200), 1)

    return frame


def is_in_rect(x, y, rect):
    return point_in_rect(x, y, rect)


def is_in_circle(x, y, circle):
    return point_in_circle(x, y, circle)
