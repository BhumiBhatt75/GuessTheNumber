"""In-memory room state for 2-player multiplayer."""

import random
from threading import Lock

from game import generate_number

MAX_ATTEMPTS = 8
_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"   # no 0/O/1/I/L
_lock = Lock()
rooms: dict = {}


# ── Room ──────────────────────────────────────────────────────────────────────

class Room:
    def __init__(self, code: str):
        self.code = code
        self.players: dict = {}   # sid -> player dict
        self.order: list = []     # turn order [sid, sid]
        self.turn_index: int = 0
        self.started: bool = False
        self.ended: bool = False
        self.winner = None        # sid or None (None = draw)

    # ── Player management ─────────────────────────────────────────────────────

    def add_player(self, sid: str, nickname: str) -> bool:
        if len(self.players) >= 2 or self.started:
            return False
        name = (nickname or "").strip()[:16] or f"Player {len(self.players) + 1}"
        self.players[sid] = {
            "sid": sid,
            "nickname": name,
            "secret": None,       # Will be set by player via number selection
            "attempts": 0,
            "best_correct": 0,
            "progress": 0,       # 0 | 25 | 50 | 75 | 100
            "won": False,
            "done": False,       # used all attempts without winning
        }
        self.order.append(sid)
        return True

    def remove_player(self, sid: str):
        self.players.pop(sid, None)
        if sid in self.order:
            self.order.remove(sid)

    # ── Game start ────────────────────────────────────────────────────────────

    def start(self) -> bool:
        if len(self.players) == 2 and not self.started:
            random.shuffle(self.order)
            self.started = True
            self.turn_index = 0
            return True
        return False

    # ── Turn management ───────────────────────────────────────────────────────

    @property
    def current_turn(self):
        if not self.started or self.ended or not self.order:
            return None
        return self.order[self.turn_index % len(self.order)]

    def advance_turn(self):
        """Move to next player; skip players that are done."""
        n = len(self.order)
        if not n:
            return
        for _ in range(n):
            self.turn_index = (self.turn_index + 1) % n
            sid = self.order[self.turn_index]
            if not self.players[sid].get("done"):
                return

    # ── Serialisation ─────────────────────────────────────────────────────────

    def public_state(self, viewer_sid=None) -> dict:
        """Safe snapshot with secrets only visible to owner."""
        return {
            "code": self.code,
            "started": self.started,
            "ended": self.ended,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "max_attempts": MAX_ATTEMPTS,
            "players": [
                {
                    "sid": p["sid"],
                    "nickname": p["nickname"],
                    "attempts": p["attempts"],
                    "progress": p["progress"],
                    "won": p["won"],
                    "done": p["done"],
                    "secret": p["secret"] if p["sid"] == viewer_sid else None,
                    "last_guess": p.get("last_guess"),
                }
                for p in self.players.values()
            ],
        }


# ── Public helpers ─────────────────────────────────────────────────────────────

def create_room() -> Room:
    with _lock:
        while True:
            code = "".join(random.choices(_CODE_CHARS, k=4))
            if code not in rooms:
                break
        room = Room(code)
        rooms[code] = room
        return room


def get_room(code: str):
    return rooms.get((code or "").strip().upper())


def find_room_by_sid(sid: str):
    for room in rooms.values():
        if sid in room.players:
            return room
    return None


def delete_room(code: str):
    rooms.pop(code, None)
