import os

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room as sio_join

from game import is_valid_number
from rooms import (
    MAX_ATTEMPTS, create_room, get_room, find_room_by_sid, delete_room,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gmiyc-dev-key-change-in-prod")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


# ── HTTP ───────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _broadcast(room, event, data):
    socketio.emit(event, data, room=room.code)


def _state(room):
    # Send personalized state to each player
    for sid in room.players.keys():
        socketio.emit("state_update", room.public_state(viewer_sid=sid), room=sid)


def _end(room, winner_sid, forfeit=False):
    room.ended = True
    room.winner = winner_sid
    _broadcast(room, "game_over", {
        "winner": winner_sid,
        "forfeit": forfeit,
        "secrets": {sid: p["secret"] for sid, p in room.players.items()},
    })


# ── Socket events ──────────────────────────────────────────────────────────────

@socketio.on("create_room")
def on_create_room(data):
    nickname = ((data or {}).get("nickname") or "").strip()
    room = create_room()
    room.add_player(request.sid, nickname)
    sio_join(room.code)
    emit("room_created", {"code": room.code, "your_sid": request.sid})
    _state(room)


@socketio.on("join_room")
def on_join_room(data):
    data = data or {}
    code     = (data.get("code")     or "").strip().upper()
    nickname = (data.get("nickname") or "").strip()

    room = get_room(code)
    if not room:
        emit("join_error", {"message": "Room not found"}); return
    if room.started:
        emit("join_error", {"message": "Game already in progress"}); return
    if len(room.players) >= 2:
        emit("join_error", {"message": "Room is full"}); return

    room.add_player(request.sid, nickname)
    sio_join(code)
    emit("join_success", {"code": code, "your_sid": request.sid})

    # Don't auto-start game - wait for both players to choose numbers
    _state(room)


@socketio.on("make_guess")
def on_guess(data):
    guess_str = str((data or {}).get("guess", "")).strip()

    room = find_room_by_sid(request.sid)
    if not room or not room.started or room.ended:
        emit("guess_error", {"message": "No active game"}); return
    if room.current_turn != request.sid:
        emit("guess_error", {"message": "Not your turn"}); return

    valid, msg = is_valid_number(guess_str)
    if not valid:
        emit("guess_error", {"message": msg}); return

    player = room.players[request.sid]
    
    # Find opponent's secret number (that's what the player should be guessing)
    opponent_sids = [sid for sid in room.players.keys() if sid != request.sid]
    if not opponent_sids:
        emit("guess_error", {"message": "No opponent found"}); return
    
    opponent_sid = opponent_sids[0]
    secret = room.players[opponent_sid]["secret"]
    
    if not secret:
        emit("guess_error", {"message": "Opponent hasn't chosen a number yet"}); return

    # Per-digit feedback
    feedback = []
    for i in range(4):
        if guess_str[i] == secret[i]:
            feedback.append("correct")
        elif guess_str[i] in secret:
            feedback.append("exists")
        else:
            feedback.append("none")

    correct = feedback.count("correct")
    player["attempts"] += 1
    
    # Track last guess
    player["last_guess"] = guess_str

    # Update progress (based on best correct-position count)
    if correct > player["best_correct"]:
        player["best_correct"] = correct
        player["progress"] = int(correct / 4 * 100)   # 0 | 25 | 50 | 75 | 100

    won = correct == 4
    if won:
        player["won"] = True
        player["progress"] = 100
    elif player["attempts"] >= MAX_ATTEMPTS:
        player["done"] = True

    # Send tile feedback only to the guesser
    emit("guess_feedback", {
        "guess": guess_str,
        "feedback": feedback,
        "correct": correct,
        "attempts": player["attempts"],
        "progress": player["progress"],
    })

    if won:
        _state(room)
        _end(room, request.sid)
        return

    # Advance turn; check for draw (all done)
    room.advance_turn()
    all_done = all(p["done"] for p in room.players.values())
    if all_done:
        _state(room)
        _end(room, None)
        return

    _state(room)


@socketio.on("confirm_number")
def on_confirm_number(data):
    number_str = str((data or {}).get("number", "")).strip()
    
    room = find_room_by_sid(request.sid)
    if not room:
        emit("number_error", {"message": "No active room"}); return
    
    valid, msg = is_valid_number(number_str)
    if not valid:
        emit("number_error", {"message": msg}); return
    
    # Update player's secret number
    if request.sid in room.players:
        room.players[request.sid]["secret"] = number_str
    
    emit("number_confirmed", {})
    
    # If both players have confirmed numbers and room has 2 players, start the game
    if len(room.players) == 2 and all(p.get("secret") for p in room.players.values()):
        room.start()
        _state(room)


@socketio.on("leave_game")
def on_leave(_data=None):
    _handle_leave(request.sid)


@socketio.on("disconnect")
def on_disconnect():
    _handle_leave(request.sid)


def _handle_leave(sid):
    room = find_room_by_sid(sid)
    if not room:
        return

    room.remove_player(sid)

    if not room.players:
        delete_room(room.code)
        return

    # Remaining player wins by forfeit if game was live
    if room.started and not room.ended:
        remaining = list(room.players.keys())[0]
        _end(room, remaining, forfeit=True)
    else:
        socketio.emit("opponent_left", {}, room=room.code)
        _state(room)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port,
                 debug=True, allow_unsafe_werkzeug=True)
