"""Stdlib HTTP server for the defense-puzzle board UI."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .game import Action, ActionType, DefenseGame
from .grid import Pos
from .puzzles import PUZZLES, PUZZLE_CATEGORIES, get_puzzle
from .solutions import solution_steps

import os

WEB_DIR = Path(__file__).resolve().parent / "web"
HOST = "127.0.0.1"
PORT = int(os.environ.get("DEFENSE_PORT", "8765"))

_sessions: dict[str, DefenseGame] = {}
_lock = threading.Lock()


def _game(session: str = "default") -> DefenseGame:
    with _lock:
        if session not in _sessions:
            _sessions[session] = DefenseGame(get_puzzle("D1"))
        return _sessions[session]


def _set_game(game: DefenseGame, session: str = "default") -> None:
    with _lock:
        _sessions[session] = game


def _parse_action(data: dict) -> Action:
    kind = data.get("type", "").lower()
    dest = None
    if data.get("x") is not None and data.get("y") is not None:
        dest = Pos(int(data["x"]), int(data["y"]))
    target_id = data.get("target_id")
    actor_id = data.get("actor_id")
    mapping = {
        "move": ActionType.MOVE,
        "dribble": ActionType.DRIBBLE,
        "pass": ActionType.PASS,
        "lob": ActionType.LOB,
        "shoot": ActionType.SHOOT,
        "end": ActionType.END_TURN,
    }
    if kind not in mapping:
        raise ValueError(f"未知動作: {kind}")
    return Action(
        type=mapping[kind],
        dest=dest,
        target_id=target_id.upper() if target_id else None,
        actor_id=actor_id.upper() if actor_id else None,
    )


class ReuseThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def server_bind(self) -> None:
        """Avoid socket.getfqdn() — it can hang on some macOS network setups."""
        from socketserver import TCPServer

        TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = host if isinstance(host, str) else "127.0.0.1"
        self.server_port = port


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:  # quieter
        pass

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/state":
            self._json(200, _game().to_dict())
            return
        if path == "/api/puzzles":
            self._json(
                200,
                {
                    "categories": [
                        {
                            "id": cat["id"],
                            "label": cat["label"],
                            "puzzles": [
                                {
                                    "id": p.id,
                                    "title": p.title,
                                    "description": p.description,
                                }
                                for p in PUZZLES
                                if p.category == cat["id"]
                            ],
                        }
                        for cat in PUZZLE_CATEGORIES
                    ],
                    "puzzles": [
                        {
                            "id": p.id,
                            "title": p.title,
                            "description": p.description,
                            "category": p.category,
                        }
                        for p in PUZZLES
                    ],
                },
            )
            return

        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        # Drop accidental query leftovers if any
        rel = rel.split("?", 1)[0]
        file_path = (WEB_DIR / rel).resolve()
        if not str(file_path).startswith(str(WEB_DIR)) or not file_path.is_file():
            self.send_error(404)
            return
        # Opening the page must NOT reset the shared game — that races with
        # an in-progress 正解示範 in another tab / soft refresh.
        data = file_path.read_bytes()
        ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in (
            "application/javascript",
            "application/json",
        ):
            ctype = f"{ctype}; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            data = self._read_json()
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "message": "Invalid JSON"})
            return

        if path == "/api/new":
            pid = data.get("puzzle_id", "D1")
            try:
                game = DefenseGame(get_puzzle(pid))
            except KeyError as e:
                self._json(400, {"ok": False, "message": str(e)})
                return
            _set_game(game)
            self._json(200, {"ok": True, "state": game.to_dict()})
            return

        if path == "/api/solution":
            pid = data.get("puzzle_id") or _game().puzzle.id
            try:
                steps = solution_steps(pid)
            except (KeyError, RuntimeError) as e:
                self._json(400, {"ok": False, "message": str(e)})
                return
            # Run the whole clear on a private board so a page reload / other
            # tab cannot clobber the shared session mid-demo.
            from .solutions import solution_actions

            game = DefenseGame(get_puzzle(pid))
            frames: list[dict] = []
            won = False
            for meta, action in zip(steps, solution_actions(pid)):
                result = game.apply(action)
                frames.append(
                    {
                        **meta,
                        "ok": result.ok,
                        "message": result.message,
                        "goal": result.goal,
                        "turnover": result.turnover,
                        "logs": result.logs,
                        "state": game.to_dict(),
                    }
                )
                if not result.ok or (result.turnover and not result.goal):
                    self._json(
                        400,
                        {
                            "ok": False,
                            "message": f"示範腳本失敗：{result.message}",
                            "puzzle_id": pid.upper(),
                            "frames": frames,
                            "state": game.to_dict(),
                        },
                    )
                    return
                if result.goal:
                    won = True
                    break
            _set_game(DefenseGame(get_puzzle(pid)))
            kickoff = _game().to_dict()
            self._json(
                200,
                {
                    "ok": True,
                    "puzzle_id": pid.upper(),
                    "steps": steps,
                    "frames": frames,
                    "won": won,
                    "state": kickoff,
                    "final_state": game.to_dict(),
                },
            )
            return

        if path == "/api/action":
            with _lock:
                game = _game()
                try:
                    action = _parse_action(data)
                    result = game.apply(action)
                except (ValueError, KeyError, StopIteration) as e:
                    self._json(
                        400,
                        {
                            "ok": False,
                            "message": str(e),
                            "state": game.to_dict(),
                        },
                    )
                    return
                payload = {
                    "ok": result.ok,
                    "message": result.message,
                    "goal": result.goal,
                    "turnover": result.turnover,
                    "logs": result.logs,
                    "state": game.to_dict(),
                }
            self._json(200, payload)
            return

        self._json(404, {"ok": False, "message": "Not found"})


def main() -> None:
    server = ReuseThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"解防守題 UI → {url}", flush=True)
    print("按 Ctrl+C 結束", flush=True)
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye", flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()
