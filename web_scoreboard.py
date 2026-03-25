# web_scoreboard.py
from flask import Flask, render_template_string
import threading

app = Flask(__name__)

_state = {
    "p1": 0,
    "p2": 0,
    "round": 1,
    "winner": None
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cornhole Scoreboard</title>
    <style>
        body { font-family: Arial; background: #111; color: #eee; text-align: center; }
        .score { font-size: 4em; margin: 20px; }
        .round { font-size: 2em; margin: 10px; }
        .winner { font-size: 3em; color: #0f0; margin: 20px; }
    </style>
</head>
<body>
    <h1>Cornhole Live Scoreboard</h1>
    <div class="round">Round: {{ round }}</div>
    <div class="score">
        Player 1: {{ p1 }} &nbsp;&nbsp; | &nbsp;&nbsp; Player 2: {{ p2 }}
    </div>
    {% if winner %}
    <div class="winner">WINNER: PLAYER {{ winner }}</div>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, **_state)


def update_scoreboard(game):
    _state["p1"] = game.total_score_p1
    _state["p2"] = game.total_score_p2
    _state["round"] = game.round_number
    _state["winner"] = game.winner if game.game_over else None


def start_server(port=8080):
    t = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
                         daemon=True)
    t.start()
