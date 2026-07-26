# 足球相對論 · 關卡海報（LaTeX）

**A1 直式**（594×841 mm）雙欄海報。

## 檔案

- `football_relativity.tex` — 原始碼（編這個）
- `football_relativity.pdf` — 編譯結果

## 編譯

```bash
cd poster
xelatex football_relativity.tex
xelatex football_relativity.tex
```

## 縮排規則（已寫進 tex）

- 正文：段首縮排 2 字（`\parindent=2em`）
- 大／小標、流程圖、表格、提示框：頂格（`\noindent`）
- 編號列表：數字與正文左緣對齊（`enumitem leftmargin=2em`）
