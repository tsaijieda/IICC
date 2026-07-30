# 足球相對論 · 關卡海報（LaTeX）

**A1 直式**（594×841 mm）雙欄海報，以及 **A4 關卡說明**（`final_document/poster.md`）。

## 檔案

- `football_relativity.tex` — A1 海報原始碼
- `football_relativity.pdf` — A1 編譯結果
- `poster.tex` — 由 `final_document/poster.md` 同步的 A4 說明（含 `1.png`、`2.png`）
- `poster.pdf` — A4 編譯結果（亦複製至 `../poster.pdf`）

## 編譯 A1 海報

```bash
cd poster
xelatex football_relativity.tex
xelatex football_relativity.tex
```

## 編譯 A4 關卡說明（final_document/poster.md）

圖片請放在 repo 根目錄：`1.png`（關卡流程）、`2.png`（場地圖）。

```bash
cd poster
xelatex poster.tex
xelatex poster.tex
cp poster.pdf ../poster.pdf
```

## 縮排規則（已寫進 tex）

- 正文：段首縮排 2 字（`\parindent=2em`）
- 大／小標、流程圖、表格、提示框：頂格（`\noindent`）
- 編號列表：數字與正文左緣對齊（`enumitem leftmargin=2em`）
