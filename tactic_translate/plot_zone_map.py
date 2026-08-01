"""Draw the 20-zone pitch map with zone numbers and Chinese names (SVG)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from .plot_run_tactic import zone_center, zone_rect
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

# SVG canvas: width fixed; height from pitch aspect.
SVG_W = 680
SVG_H = int(SVG_W * PITCH_L / PITCH_W)
MARGIN = 28

ZONE_COLORS = {
    2: "#c8e6c9",
    20: "#c8e6c9",
    18: "#fff9c4",
    19: "#fff9c4",
}
DEFAULT_ZONE_COLOR = "#e8f5e9"
PASS_COLOR = "#ff6f00"
TOUCH_COLOR = "#1565c0"


def _touch_anchor(zid: int) -> tuple[float, float]:
    """Slightly offset touch markers from zone center to avoid base-map labels."""
    x, y, w, h = zone_rect(zid)
    cx, cy = x + w / 2, y + h / 2
    ox = w * 0.28 if cx < PITCH_W / 2 else -w * 0.28
    oy = h * 0.22
    return cx + ox, cy + oy


def _pass_label_offset(x1: float, y1: float, x2: float, y2: float, dist: float = 2.8) -> tuple[float, float]:
    dx, dy = x2 - x1, y2 - y1
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    return -dy / length * dist, dx / length * dist


def _sx(x: float) -> float:
    return MARGIN + x / PITCH_W * (SVG_W - 2 * MARGIN)


def _sy(y: float) -> float:
    return MARGIN + y / PITCH_L * (SVG_H - 2 * MARGIN)


def _rect_svg(x: float, y: float, w: float, h: float, **attrs: str) -> str:
    ax, ay = _sx(x), _sy(y)
    aw, ah = w / PITCH_W * (SVG_W - 2 * MARGIN), h / PITCH_L * (SVG_H - 2 * MARGIN)
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<rect x="{ax:.2f}" y="{ay:.2f}" width="{aw:.2f}" height="{ah:.2f}" {parts}/>'


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


def _pct_to_m(rect: dict) -> tuple[float, float, float, float]:
    x = rect["x"] / 100 * PITCH_W
    y = rect["y"] / 100 * PITCH_L
    w = rect["w"] / 100 * PITCH_W
    h = rect["h"] / 100 * PITCH_L
    return x, y, w, h


def _font_size_svg(w_m: float, h_m: float, cap: float) -> float:
    aw = w_m / PITCH_W * (SVG_W - 2 * MARGIN)
    ah = h_m / PITCH_L * (SVG_H - 2 * MARGIN)
    return max(8.0, min(cap, min(aw, ah) * 0.2))


def _zone_border_toward(z_from: int, z_to: int) -> tuple[float, float]:
    """Point on z_from's border along the ray toward z_to (keeps lines off zone labels)."""
    x, y, w, h = zone_rect(z_from)
    cx, cy = x + w / 2, y + h / 2
    tx, ty = zone_center(z_to)
    dx, dy = tx - cx, ty - cy
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return cx, cy
    scale_x = (w / 2) / abs(dx) if abs(dx) > 1e-9 else float("inf")
    scale_y = (h / 2) / abs(dy) if abs(dy) > 1e-9 else float("inf")
    t = min(scale_x, scale_y) * 0.92
    return cx + dx * t, cy + dy * t


def _append_zone_map_base(lines: list[str], *, title: str, extra_height: int = 0) -> None:
    total_h = SVG_H + extra_height
    lines.extend(
        [
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
    )

    for rect in ZONE_RECTS:
        zid = int(rect["zone"])
        x, y, w, h = _pct_to_m(rect)
        color = ZONE_COLORS.get(zid, DEFAULT_ZONE_COLOR)
        lines.append(
            _rect_svg(
                x, y, w, h,
                fill=color,
                stroke="#1b5e20",
                **{"stroke-width": "1", "opacity": "0.88"},
            )
        )
        cx, cy = x + w / 2, y + h / 2
        fs_num = _font_size_svg(w, h, 13)
        fs_name = _font_size_svg(w, h, 11)
        lines.append(
            _text_svg(
                cx, cy - h * 0.06,
                f"Zone {zid}",
                **{
                    "text-anchor": "middle",
                    "dominant-baseline": "middle",
                    "font-size": f"{fs_num:.1f}",
                    "font-weight": "bold",
                    "fill": "#1b5e20",
                },
            )
        )
        lines.append(
            _text_svg(
                cx, cy + h * 0.12,
                ZONE_NAMES.get(zid, f"區域{zid}"),
                **{
                    "text-anchor": "middle",
                    "dominant-baseline": "middle",
                    "font-size": f"{fs_name:.1f}",
                    "fill": "#263238",
                },
            )
        )

    lw = "1.4"
    lines += [
        _rect_svg(0, 0, PITCH_W, PITCH_L, fill="none", stroke="white", **{"stroke-width": lw}),
        _line_svg(0, HALFWAY_Y, PITCH_W, HALFWAY_Y, stroke="white", **{"stroke-width": lw}),
        _rect_svg(WING_W, 0, PA_WIDTH, PA_DEPTH, fill="none", stroke="white", **{"stroke-width": lw}),
        _rect_svg(
            WING_W, PITCH_L - PA_DEPTH, PA_WIDTH, PA_DEPTH,
            fill="none", stroke="white", **{"stroke-width": lw},
        ),
    ]
    goal_w = 7.32
    gx = (PITCH_W - goal_w) / 2
    lines += [
        _line_svg(gx, 0, gx + goal_w, 0, stroke="white", **{"stroke-width": "3"}),
        _line_svg(gx, PITCH_L, gx + goal_w, PITCH_L, stroke="white", **{"stroke-width": "3"}),
    ]


def _circle_svg(x: float, y: float, r: float, **attrs: str) -> str:
    parts = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f'<circle cx="{_sx(x):.2f}" cy="{_sy(y):.2f}" r="{r:.2f}" {parts}/>'


def build_zone_map_svg() -> str:
    lines: list[str] = []
    _append_zone_map_base(lines, title="戰術區域圖（Zones 1–20）", extra_height=36)
    lines.append(
        _text_svg(
            PITCH_W / 2, -3.5,
            "↑ 進攻方向（對手球門）",
            **{"text-anchor": "middle", "font-size": "11", "fill": "#546e7a"},
        )
    )
    lines.append("</svg>")
    return "\n".join(lines)


def _load_play_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rt = data.get("run_tactic") or {}
    pass_points = data.get("pass_points") or data.get("frames") or []
    return {
        "play_id": data.get("play_id", path.stem),
        "title": data.get("title", ""),
        "pass_points": pass_points,
        "defenders": rt.get("defenders") or [],
        "reception_radius_m": float(rt.get("reception_radius_m", 1.0)),
    }


def build_play_on_zone_map_svg(
    *,
    title: str,
    pass_points: list[dict[str, Any]],
    reception_radius_m: float = 1.0,
) -> str:
    """Zone map with on-pitch route overlay (labels slightly offset from zone centers)."""
    lines: list[str] = []
    _append_zone_map_base(lines, title=title, extra_height=40)

    pts = [_touch_anchor(int(p["zone"])) for p in pass_points]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        action = pass_points[i + 1].get("pass_action", "傳球")
        lines.append(
            _line_svg(
                x1, y1, x2, y2,
                stroke=PASS_COLOR,
                **{"stroke-width": "2.5", "stroke-dasharray": "6 4", "opacity": "0.9"},
            )
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ox, oy = _pass_label_offset(x1, y1, x2, y2)
        lines.append(
            _text_svg(
                mx + ox, my + oy,
                action,
                **{
                    "text-anchor": "middle",
                    "font-size": "12",
                    "font-weight": "bold",
                    "fill": PASS_COLOR,
                },
            )
        )

    r_px = reception_radius_m / PITCH_W * (SVG_W - 2 * MARGIN) * 0.9
    for i, p in enumerate(pass_points):
        zid = int(p["zone"])
        ax, ay = _touch_anchor(zid)
        label = chr(0x2460 + i) if i < 20 else str(i + 1)
        role = p.get("receiver") or p.get("label", "")
        outcome = p.get("outcome", "")
        lines.append(
            _circle_svg(ax, ay, r_px, fill="none", stroke=TOUCH_COLOR, **{"stroke-width": "2.5"})
        )
        lines.append(
            _circle_svg(ax, ay, 6.0, fill=TOUCH_COLOR, stroke="white", **{"stroke-width": "1"})
        )
        lines.append(
            _text_svg(
                ax, ay - 3.2,
                label,
                **{
                    "text-anchor": "middle",
                    "font-size": "14",
                    "font-weight": "bold",
                    "fill": TOUCH_COLOR,
                },
            )
        )
        if role:
            sub = f"{role}{('·' + outcome) if outcome else ''}"
            lines.append(
                _text_svg(
                    ax, ay + 3.8,
                    sub,
                    **{"text-anchor": "middle", "font-size": "13", "fill": "#0d47a1"},
                )
            )

    lines.append("</svg>")
    return "\n".join(lines)


def write_play_on_zone_map(yaml_path: Path, out_dir: Path | None = None) -> Path:
    spec = _load_play_yaml(yaml_path)
    if not spec["pass_points"]:
        raise ValueError(f"No pass_points in {yaml_path}")
    svg = build_play_on_zone_map_svg(
        title=f"{spec['play_id']} · {spec['title']}",
        pass_points=spec["pass_points"],
        reception_radius_m=spec["reception_radius_m"],
    )
    root = _output_dir(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"{spec['play_id']}_zone_map.svg"
    out.write_text(svg, encoding="utf-8")
    return out


ROOT = Path(__file__).resolve().parent.parent
FINAL_DOC = ROOT / "final_document"


def _output_dir(out_dir: Path | None) -> Path:
    return out_dir or FINAL_DOC


def write_zone_map(out_dir: Path | None = None) -> Path:
    root = _output_dir(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    svg_path = root / "zone_map.svg"
    svg_path.write_text(build_zone_map_svg(), encoding="utf-8")
    return svg_path


def write_zone_map_pdf(out_dir: Path | None = None) -> Path:
    """Render zone map as PDF (matplotlib)."""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.patches import Rectangle

    root = _output_dir(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    pdf_path = root / "zone_map.pdf"

    for family in ("PingFang TC", "Heiti TC", "Songti SC", "Arial Unicode MS"):
        try:
            font_manager.findfont(family, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [family]
            break
        except ValueError:
            continue
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(6.8, 10.5))
    ax.set_xlim(0, PITCH_W)
    ax.set_ylim(PITCH_L, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), PITCH_W, PITCH_L, facecolor="#2e7d32", edgecolor="white", lw=1.4))

    for rect in ZONE_RECTS:
        zid = int(rect["zone"])
        x, y, w, h = _pct_to_m(rect)
        color = ZONE_COLORS.get(zid, DEFAULT_ZONE_COLOR)
        ax.add_patch(
            Rectangle(
                (x, y), w, h,
                facecolor=color, edgecolor="#1b5e20", lw=1, alpha=0.88,
            )
        )
        cx, cy = x + w / 2, y + h / 2
        fs = max(6, min(9, min(w, h) * 0.35))
        ax.text(cx, cy - h * 0.05, f"Zone {zid}", ha="center", va="center",
                fontsize=fs, fontweight="bold", color="#1b5e20")
        name = ZONE_NAMES.get(zid, f"區域{zid}")
        ax.text(cx, cy + h * 0.1, name, ha="center", va="center",
                fontsize=max(5.5, fs - 1), color="#263238")

    wg = WING_W
    ax.plot([0, PITCH_W], [HALFWAY_Y, HALFWAY_Y], color="white", lw=1.2)
    ax.add_patch(Rectangle((wg, 0), PA_WIDTH, PA_DEPTH, fill=False, edgecolor="white", lw=1.2))
    ax.add_patch(Rectangle((wg, PITCH_L - PA_DEPTH), PA_WIDTH, PA_DEPTH, fill=False, edgecolor="white", lw=1.2))
    goal_w = 7.32
    gx = (PITCH_W - goal_w) / 2
    ax.plot([gx, gx + goal_w], [0, 0], color="white", lw=2.5)
    ax.plot([gx, gx + goal_w], [PITCH_L, PITCH_L], color="white", lw=2.5)
    ax.set_title("戰術區域圖（Zones 1–20）\n↑ 進攻方向（對手球門）", fontsize=12, pad=12)

    fig.tight_layout()
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw zone map SVG with numbers and names.")
    parser.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=FINAL_DOC,
        help="Output directory (default: final_document/)",
    )
    parser.add_argument("--pdf", action="store_true", help="Also write zone_map.pdf")
    parser.add_argument(
        "--play",
        type=Path,
        metavar="YAML",
        help="Overlay pass points from a play YAML onto the zone map",
    )
    args = parser.parse_args()
    if args.play:
        path = write_play_on_zone_map(args.play, args.out_dir)
        print(f"Wrote {path}")
        return
    path = write_zone_map(args.out_dir)
    print(f"Wrote {path}")
    if args.pdf:
        pdf = write_zone_map_pdf(args.out_dir)
        print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()
