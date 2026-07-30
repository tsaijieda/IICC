"""Export A001–A006 tactical language (description + evaluation_points) to PDF."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FINAL_DOC = ROOT / "final_document"
DEFAULT_PLAYS = tuple(f"A{i:03d}" for i in range(1, 7))
TEX_NAME = "A001-A006_戰術語言.tex"
PDF_NAME = "A001-A006_戰術語言.pdf"


def _latex_escape(text: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(repl.get(ch, ch) for ch in text)


def _load_play(play_id: str) -> dict:
    path = FINAL_DOC / f"{play_id.lower()}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _play_section(play: dict) -> str:
    play_id = play.get("play_id", "")
    title = _latex_escape(play.get("title", ""))
    description = _latex_escape(play.get("description", ""))
    return (
        f"\\subsection*{{{play_id}　{title}}}\n"
        f"\\noindent\\textbf{{戰術語言}}　{description}\n"
        f"\\vspace{{0.5em}}\n"
    )


def build_tex(play_ids: tuple[str, ...] = DEFAULT_PLAYS) -> str:
    plays = [_load_play(pid) for pid in play_ids]
    body = "\n".join(_play_section(p) for p in plays)
    return f"""% !TEX program = xelatex
% 由 tactic_translate.export_plays_pdf 產生；勿手動編輯
% 編譯：cd final_document && xelatex {TEX_NAME}
\\documentclass[10pt]{{article}}
\\usepackage[a4paper,margin=1.6cm]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xeCJK}}
\\usepackage{{titlesec}}

\\setmainfont{{Times New Roman}}
\\IfFontExistsTF{{Songti TC}}{{
  \\setCJKmainfont{{Songti TC}}
  \\setCJKsansfont{{Heiti TC}}
}}{{
  \\setCJKmainfont{{FandolSong}}
  \\setCJKsansfont{{FandolHei}}
}}

\\titlespacing*{{\\subsection}}{{0pt}}{{0.6em}}{{0.25em}}
\\titleformat{{\\subsection}}{{\\normalsize\\bfseries}}{{}}{{0em}}{{}}
\\setlength{{\\parskip}}{{0.25em}}
\\pagestyle{{empty}}

\\begin{{document}}

{{\\Large\\bfseries 戰術復刻　A001–A006 戰術語言\\par}}
\\vspace{{0.6em}}

{body}
\\end{{document}}
"""


def write_tex(play_ids: tuple[str, ...] = DEFAULT_PLAYS) -> Path:
    tex_path = FINAL_DOC / TEX_NAME
    tex_path.write_text(build_tex(play_ids), encoding="utf-8")
    return tex_path


def compile_pdf(tex_path: Path | None = None) -> Path:
    tex_path = tex_path or (FINAL_DOC / TEX_NAME)
    for _ in range(2):
        subprocess.run(
            ["xelatex", "-interaction=nonstopmode", tex_path.name],
            cwd=FINAL_DOC,
            check=True,
            capture_output=True,
        )
    return FINAL_DOC / PDF_NAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export A001–A006 戰術語言 PDF")
    parser.add_argument(
        "--plays",
        nargs="+",
        default=list(DEFAULT_PLAYS),
        help="play ids (default: A001 … A006)",
    )
    parser.add_argument("--tex-only", action="store_true", help="only write .tex")
    args = parser.parse_args(argv)

    play_ids = tuple(args.plays)
    tex_path = write_tex(play_ids)
    print(f"已寫入 {tex_path}")
    if args.tex_only:
        return 0

    try:
        pdf_path = compile_pdf(tex_path)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    print(f"已產出 {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
