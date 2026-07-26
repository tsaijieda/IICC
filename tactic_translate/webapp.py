"""Web UI for tactical-board → 戰術語言 translation."""

from __future__ import annotations

import json
import mimetypes
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from urllib.parse import urlparse

import yaml

from .io import board_from_dict, result_to_dict
from .translator import translate_board
from .zones import PITCH_ASPECT, ZONE_CELLS, ZONE_LAYOUT, ZONE_NAMES, ZONE_RECTS, ZONES

WEB_DIR = Path(__file__).resolve().parent / "web"
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "boards"
HOST = "127.0.0.1"
PORT = int(os.environ.get("TACTIC_PORT", "8770"))


class ReuseThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def server_bind(self) -> None:
        TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = host if isinstance(host, str) else "127.0.0.1"
        self.server_port = port


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
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

        if path == "/api/zones":
            self._json(
                200,
                {
                    "layout": ZONE_LAYOUT,
                    "cells": ZONE_CELLS,
                    "rows": 6,
                    "cols": 5,
                    "pitch_aspect": PITCH_ASPECT,
                    "zone_rects": ZONE_RECTS,
                    "zones": {
                        str(zid): {
                            "name": ZONE_NAMES.get(zid, ""),
                            "depth": z.depth,
                            "lane": z.lane,
                            "half_space": z.half_space,
                            "in_box": z.in_box,
                        }
                        for zid, z in ZONES.items()
                    },
                },
            )
            return

        if path == "/api/examples":
            items = []
            if EXAMPLES_DIR.is_dir():
                for p in sorted(EXAMPLES_DIR.glob("*.yaml")):
                    items.append({"id": p.stem, "file": p.name})
            self._json(200, {"examples": items})
            return

        if path.startswith("/api/examples/"):
            name = path.split("/")[-1]
            fp = EXAMPLES_DIR / f"{name}.yaml"
            if not fp.is_file():
                fp = EXAMPLES_DIR / name
            if not fp.is_file():
                self._json(404, {"error": "not found"})
                return
            data = yaml.safe_load(fp.read_text(encoding="utf-8"))
            self._json(200, data)
            return

        if path in ("/", "/index.html"):
            path = "/index.html"
        rel = path.lstrip("/")
        fp = WEB_DIR / rel
        if not fp.is_file() or WEB_DIR not in fp.resolve().parents:
            self.send_error(404)
            return
        ctype, _ = mimetypes.guess_type(str(fp))
        body = fp.read_bytes()
        self.send_response(200)
        if ctype:
            self.send_header("Content-Type", f"{ctype}; charset=utf-8" if ctype.startswith("text/") else ctype)
        if rel.endswith((".js", ".html", ".css")):
            self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/translate":
            self.send_error(404)
            return
        data = self._read_json()
        board = board_from_dict(data)
        result = translate_board(board)
        self._json(200, result_to_dict(result))


def main() -> None:
    server = ReuseThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"戰術轉譯 UI → {url}")
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
