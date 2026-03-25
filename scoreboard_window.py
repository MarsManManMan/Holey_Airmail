import cv2
import numpy as np

def run_scoreboard(game, ui_state):
    cv2.namedWindow("SCOREBOARD", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("SCOREBOARD", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        frame = np.zeros((1080,1920,3), dtype=np.uint8)

        # Achtergrond
        cv2.rectangle(frame,(0,0),(960,1080),(30,30,30),-1)
        cv2.rectangle(frame,(960,0),(1920,1080),(50,50,50),-1)

        # P1
        cv2.putText(frame,"PLAYER 1",(180,150),cv2.FONT_HERSHEY_DUPLEX,2.2,(255,255,255),4)
        cv2.putText(frame,str(game.total_score_p1),(300,650),cv2.FONT_HERSHEY_DUPLEX,8,(0,255,255),12)

        # P2
        cv2.putText(frame,"PLAYER 2",(1140,150),cv2.FONT_HERSHEY_DUPLEX,2.2,(255,255,255),4)
        cv2.putText(frame,str(game.total_score_p2),(1260,650),cv2.FONT_HERSHEY_DUPLEX,8,(0,255,255),12)

        # Status
        status = "RUNNING" if ui_state["running"] else "PAUSED"
        cv2.putText(frame,status,(740,950),cv2.FONT_HERSHEY_DUPLEX,2,(0,255,0),4)

        cv2.imshow("SCORE-BOARD", frame)
        if cv2.waitKey(1) == 27:
            break
