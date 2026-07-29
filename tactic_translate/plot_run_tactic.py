"""Draw run-tactic setup diagrams (score cones + static defenders)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from .zones import (
    HALFWAY_Y,
    PA_DEPTH,
    PA_WIDTH,
    PITCH_L,
    PITCH_W,
    WING_W,
    ZONE_NAMES,
    ZONE_RECTS,
)

SVG_W = 680
SVG_H = int(SVG_W * PITCH_L / PITCH_W)
MARGIN = 28
LEGEND_H = 72

SCORE_COLOR = "#1565c0"
DEF_COLOR = "#c62828"
PASS_COLOR = "#ff6f00"


def _sx(x: float) -> float:
    return MARGIN + x / PITCH_W * (SVG_W - 2 * MARGIN)


def _sy(y: float) -> float:
    return MARGIN + y / PITCH_L * (SVG_H - 2 * MARGIN)


def _pct_to_m(rect: dict) -> tuple[float, float, float, float]:
    x = rect["x"] / 100 * PITCH_W
    y = rect["y"] / 100 * PITCH_L
    w = rect["w"] / 100 * PITCH_W
    h = rect["h"] / 100 * PITCH_L
    return x, y, w, h


def zone_rect(zid: int) -> tuple[float, float, float, float]:
    for rect in ZONE_RECTS:
        if int(rect["zone"]) == zid:
            return _pct_to_m(rect)
    raise KeyError(zid)


def zone_center(zid: int) -> tuple[float, float]:
    x, y, w, h = zone_rect(zid)
    return x + w / 2, y + h / 2


def edge_midpoint(z_a: int, z_b: int) -> tuple[float, float]:
    x0, y0, w0, h0 = zone_rect(z_a)
    x1, y1, w1, h1 = zone_rect(z_b)
    eps = 0.05
    # vertical shared edge
    if abs((x0 + w0) - x1) < eps or abs((x1 + w1) - x0) < eps:
        ex = (x0 + w0 + x1) / 2 if abs((x0 + w0) - x1) < eps else (x1 + w1 + x0) / 2
        oy0, oy1 = max(y0, y1), min(y0 + h0, y1 + h1)
        return ex, (oy0 + oy1) / 2
    # horizontal shared edge
    if abs((y0 + h0) - y1) < eps or abs((y1 + h1) - y0) < eps:
        ey = (y0 + h0 + y1) / 2 if abs((y0 + h0) - y1) < eps else (y1 + h1 + y0) / 2
        ox0, ox1 = max(x0, x1), min(x0 + w0, x1 + w1)
        return (ox0 + ox1) / 2, ey
    # fallback: midpoint between centers
    c0, c1 = zone_center(z_a), zone_center(z_b)
    return (c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2


def defender_xy(defn: dict[str, Any]) -> tuple[float, float]:
    if "between" in defn:
        a, b = defn["between"]
        return edge_midpoint(int(a), int(b))
    if "zone" in defn:
        return zone_center(int(defn["zone"]))
    return float(defn["x"]), float(defn["y"])


def _circle_svg(x: float, y: float, r: float, **attrs: str) -> str:
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<circle cx="{_sx(x):.2f}" cy="{_sy(y):.2f}" r="{r:.2f}" {parts}/>'


def _line_svg(x1: float, y1: float, x2: float, y2: float, **attrs: str) -> str:
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return (
        f'<line x1="{_sx(x1):.2f}" y1="{_sy(y1):.2f}" '
        f'x2="{_sx(x2):.2f}" y2="{_sy(y2):.2f}" {parts}/>'
    )


def _text_svg(x: float, y: float, text: str, **attrs: str) -> str:
    esc = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<text x="{_sx(x):.2f}" y="{_sy(y):.2f}" {parts}>{esc}</text>'


def _rect_svg(x: float, y: float, w: float, h: float, **attrs: str) -> str:
    ax, ay = _sx(x), _sy(y)
    aw, ah = w / PITCH_W * (SVG_W - 2 * MARGIN), h / PITCH_L * (SVG_H - 2 * MARGIN)
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<rect x="{ax:.2f}" y="{ay:.2f}" width="{aw:.2f}" height="{ah:.2f}" {parts}/>'


def build_run_tactic_svg(
    *,
    title: str,
    score_touches: list[dict[str, Any]],
    defenders: list[dict[str, Any]],
    highlight_zones: list[int] | None = None,
    reception_radius_m: float = 1.0,
) -> str:
    total_h = SVG_H + LEGEND_H + 24
    hl = set(highlight_zones or [])
    for t in score_touches:
        hl.add(int(t["zone"]))

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {total_h}" '
        f'width="{SVG_W}" height="{total_h}">',
        "<style>",
        "  text { font-family: 'PingFang TC', 'Heiti TC', 'Noto Sans TC', sans-serif; }",
        "</style>",
        f'<rect width="100%" height="100%" fill="#fafafa"/>',
        f'<text x="{SVG_W / 2:.1f}" y="18" text-anchor="middle" font-size="15" '
        f'font-weight="bold" fill="#263238">{title}</text>',
        _rect_svg(0, 0, PITCH_W, PITCH_L, fill="#2e7d32", stroke="none"),
    ]

    for rect in ZONE_RECTS:
        zid = int(rect["zone"])
        x, y, w, h = _pct_to_m(rect)
        fill = "#bbdefb" if zid in hl else "#e8f5e9"
        opacity = "0.95" if zid in hl else "0.55"
        lines.append(
            _rect_svg(
                x, y, w, h,
                fill=fill,
                stroke="#1b5e20",
                **{"stroke-width": "1.2" if zid in hl else "0.8", "opacity": opacity},
            )
        )
        if zid in hl:
            cx, cy = x + w / 2, y + h / 2
            lines.append(
                _text_svg(
                    cx, cy,
                    f"{zid}",
                    **{
                        "text-anchor": "middle",
                        "dominant-baseline": "middle",
                        "font-size": "10",
                        "font-weight": "bold",
                        "fill": "#0d47a1",
                    },
                )
            )

    lw = "1.2"
    lines += [
        _rect_svg(0, 0, PITCH_W, PITCH_L, fill="none", stroke="white", **{"stroke-width": lw}),
        _line_svg(0, HALFWAY_Y, PITCH_W, HALFWAY_Y, stroke="white", **{"stroke-width": lw}),
        _rect_svg(WING_W, 0, PA_WIDTH, PA_DEPTH, fill="none", stroke="white", **{"stroke-width": lw}),
        _rect_svg(
            WING_W, PITCH_L - PA_DEPTH, PA_WIDTH, PA_DEPTH,
            fill="none", stroke="white", **{"stroke-width": lw},
        ),
    ]

    # pass arrows between scored touches in order
    pts = [zone_center(int(t["zone"])) for t in sorted(score_touches, key=lambda t: t.get("touch", 0))]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        lines.append(
            _line_svg(
                x1, y1, x2, y2,
                stroke=PASS_COLOR,
                **{"stroke-width": "2", "stroke-dasharray": "6 4", "opacity": "0.85"},
            )
        )

    r_px = reception_radius_m / PITCH_W * (SVG_W - 2 * MARGIN)
    for t in sorted(score_touches, key=lambda x: x.get("touch", 0)):
        zid = int(t["zone"])
        cx, cy = zone_center(zid)
        label = t.get("label") or f"評分{t.get('touch', 0) + 1}"
        role = t.get("receiver", "")
        lines.append(
            _circle_svg(cx, cy, r_px, fill="none", stroke=SCORE_COLOR, **{"stroke-width": "2.5"})
        )
        lines.append(
            _circle_svg(cx, cy, 5, fill=SCORE_COLOR, stroke="white", **{"stroke-width": "1"})
        )
        lines.append(
            _text_svg(
                cx, cy - 2.8,
                label,
                **{
                    "text-anchor": "middle",
                    "font-size": "9",
                    "font-weight": "bold",
                    "fill": SCORE_COLOR,
                },
            )
        )
        if role:
            lines.append(
                _text_svg(
                    cx, cy + 3.2,
                    role,
                    **{
                        "text-anchor": "middle",
                        "font-size": "9",
                        "fill": "#0d47a1",
                    },
                )
            )

    for i, d in enumerate(defenders, 1):
        dx, dy = defender_xy(d)
        lines.append(_circle_svg(dx, dy, 7, fill=DEF_COLOR, stroke="#4a0000", **{"stroke-width": "1.5"}))
        lines.append(
            _text_svg(
                dx, dy,
                f"D{i}",
                **{
                    "text-anchor": "middle",
                    "dominant-baseline": "middle",
                    "font-size": "8",
                    "font-weight": "bold",
                    "fill": "white",
                },
            )
        )
        note = d.get("note", "")
        if note:
            lines.append(
                _text_svg(
                    dx + 4, dy,
                    note,
                    **{"font-size": "7.5", "fill": DEF_COLOR},
                )
            )

    ly = SVG_H + 14
    lines += [
        f'<rect x="12" y="{ly}" width="{SVG_W - 24}" height="{LEGEND_H - 8}" '
        f'rx="6" fill="white" stroke="#cfd8dc"/>',
        f'<circle cx="32" cy="{ly + 18}" r="6" fill="none" stroke="{SCORE_COLOR}" stroke-width="2"/>',
        f'<text x="48" y="{ly + 22}" font-size="10" fill="#37474f">'
        f"評分接球圈（半徑 {reception_radius_m}m；只判這幾拍）</text>",
        f'<circle cx="32" cy="{ly + 40}" r="7" fill="{DEF_COLOR}"/>',
        f'<text x="48" y="{ly + 44}" font-size="10" fill="#37474f">'
        f"靜止防守圓柱（傳球碰到 = 該次失敗）</text>",
        f'<line x1="28" y1="{ly + 58}" x2="44" y2="{ly + 58}" stroke="{PASS_COLOR}" '
        f'stroke-width="2" stroke-dasharray="6 4"/>',
        f'<text x="48" y="{ly + 62}" font-size="10" fill="#37474f">正解傳球方向（示意）</text>',
        "</svg>",
    ]
    return "\n".join(lines)


def load_run_tactic_from_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rt = data.get("run_tactic") or {}
    return {
        "play_id": data.get("play_id", path.stem),
        "title": data.get("title", ""),
        "score_touches": rt.get("score_touches") or [],
        "defenders": rt.get("defenders") or [],
        "reception_radius_m": float(rt.get("reception_radius_m", 1.0)),
    }


def write_run_tactic_diagram(yaml_path: Path, out_dir: Path | None = None) -> Path:
    spec = load_run_tactic_from_yaml(yaml_path)
    if not spec["score_touches"]:
        raise ValueError(f"No run_tactic.score_touches in {yaml_path}")

    highlight = [int(t["zone"]) for t in spec["score_touches"]]
    for d in spec["defenders"]:
        if "zone" in d:
            highlight.append(int(d["zone"]))
        if "between" in d:
            highlight.extend(int(z) for z in d["between"])

    svg = build_run_tactic_svg(
        title=f"{spec['play_id']} 跑戰術場地圖 · {spec['title']}",
        score_touches=spec["score_touches"],
        defenders=spec["defenders"],
        highlight_zones=highlight,
        reception_radius_m=spec["reception_radius_m"],
    )

    root = out_dir or Path(__file__).resolve().parent.parent / "run_tactic_figures"
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{spec['play_id']}_run_tactic.svg"
    out.write_text(svg, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw run-tactic setup diagram from YAML.")
    parser.add_argument("yaml", type=Path, nargs="+", help="Question YAML paths")
    parser.add_argument("-o", "--out-dir", type=Path, default=None)
    args = parser.parse_args()
    for path in args.yaml:
        out = write_run_tactic_diagram(path, args.out_dir)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
