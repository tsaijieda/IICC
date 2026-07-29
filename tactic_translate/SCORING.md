# 評分程式說明

本文件說明 `tactic_translate/` 如何把學生畫的傳球點（`pass_points`）轉成 `TouchRecord` 時間軸，再依題目 YAML 的 `scoring:` rubric 自動給分。

戰術名詞與畫跑位規則見 [`1st_half_rules.md`](../1st_half_rules.md)；本文件只講**程式怎麼評**。

---

## 整體流程

```
BoardInput（frames[]）
    │
    ├─ validate_board()          檢查 zone 合法、至少 2 拍
    │
    ├─ build_touches()             每 frame → TouchRecord
    │     （推斷 passer、邊、結果）
    │
    ├─ load_rubric_for_play_id()  讀 a001.yaml 等 scoring: 區塊
    │
    └─ score_touches()           逐項比對 → ScoringResult
```

入口：`translate_board()`（`translator.py`）。Web UI（`play_translate.py`）與 CLI（`translate_tactics.py`）都呼叫它。

若題目 YAML **沒有** `scoring:` 區塊，`result.scoring` 為 `None`（仍會產生文字描述與 `evaluation_points`）。

---

## 第一步：建立 Touch 時間軸

`build_touches()`（`touches.py`）把 `frames` 裡**每一拍接球**變成一筆 `TouchRecord`：

| 欄位 | 來源 |
|------|------|
| `receiver_id` | frame 的 `receiver` |
| `zone` / `place` | frame 的 `zone` → `zone_name()` |
| `passer_id` | frame 的 `passer`，或上一拍 `receiver`（同一人盤帶時為自己） |
| `pass_action`（邊） | frame 若有 `pass_action` 用手填；否則 `_infer_pass_action()` 自動推斷 |
| `outcome` | frame 若有 `outcome` 用手填；否則 `_detect_outcome()` 自動推斷 |

**邊的推斷**（`_infer_pass_action`）：

1. 同一 `receiver`、球區變了 → `盤帶推進`
2. 否則跑 `detect_ball_path_tactics()`（`patterns.py`），分數 ≥ 0.67 的戰術名（傳中、直塞、回做球…）
3. 再試 `detect_basic_action()`
4. 預設 → `傳球`

**結果的推斷**（`_detect_outcome`）：

- 接球點在禁區（`BOX`）且前一拍是底線或邊為 `傳中` → `得分`
- 前一拍已在禁區內 → `得分`
- 其他進禁區 → `射正`

評分比對的是**推斷後**的 `pass_action` / `outcome`，不是學生手填的 label。

---

## 評分模式

| 模式 | `grading_mode` | 滿分 |
|------|----------------|------|
| 畫跑位 | `draw_runs`（預設） | 15 |
| 跑戰術 | `run_tactic` | 30 |

題目 YAML 的 `scoring:` 以 **畫跑位 15 分** 為基準撰寫；選跑戰術時各項配分自動加倍（滿分 30）。Web UI 左側可切換模式；API 請求 body 帶 `grading_mode`。

`load_rubric_for_play_id(play_id)` 依 `play_id` 找題目檔，例如 `A001` → `a001.yaml`。

`scoring:` 區塊範例（`a001.yaml`）：

```yaml
scoring:
  total: 15
  weights:
    players: 0.3    # 傳球人對不對
    action: 0.5     # 邊（＋若有 outcome 一併比）
    place: 0.2      # 接球點
  items:
    - name: 傳球
      points: 7.5
      touch: 1              # 0-based：看 touches[1]
      check:
        passer: AM
        receiver: FB
        action: 傳球
        place: 右路底線
    - name: 傳中
      points: 7.5
      touch: 2
      check:
        passer: FB
        receiver: ST
        action: 傳中
        place: 禁區中央
        outcome: 得分
```

`check` 也可寫在 item 頂層（與 `check:` 子鍵等價）。支援欄位：

| check 欄位 | 比對對象 |
|------------|----------|
| `passer` / `receiver` | `TouchRecord.passer_id` / `receiver_id` |
| `action`（或 `pass_action`） | `TouchRecord.pass_action` |
| `place` | `TouchRecord.place`（中文區域名） |
| `zone` | `TouchRecord.zone`（1–20 整數） |
| `outcome` | `TouchRecord.outcome` |
| `from_place` | **上一拍**的 `place`（起點，額外半權重） |

`touch` 也可用 `touch_index` 這個鍵名。

---

## 第三步：逐項評分

`score_item()`（`scoring.py`）對 rubric 的**每一個 item**：

### 固定拍次（fixed touch index）

`touch: N` 表示**只評** `touches[N]`，不會在時間軸裡「找最像的一拍」對齊。

- **多畫的拍**：不影響已指定 index 的評分（不扣分）
- **少畫的拍**：該 index 不存在 → 該項 0 分，細項顯示「缺少此拍」

例：A001 三拍（index 0/1/2）只評 touch 1 與 touch 2；index 0（AM 接球）不計分。

### 部分給分（partial credit）

每個 item 滿分為 `points`。`check` 裡**實際出現的條件**會依 `weights` 重新正規化後分配：

| 條件鍵 | 預設權重 | 比對內容 |
|--------|----------|----------|
| `players` | 30% | `passer` + `receiver` 同時正確 |
| `action` | 50% | `pass_action`；若 `check` 含 `outcome`，邊與結果須**同時**對才拿這 50% |
| `place` | 20% | `place` 和／或 `zone`（有寫才比） |

若 `check` 只有 `action`，該項 100% 只看邊。若沒有任何可評條件，預設整項只看 `action`。

單條件錯只扣對應比例，其餘條件仍給分。

### A001 滿分範例

```yaml
frames:
  - {zone: 15, receiver: AM}   # touch 0：不評
  - {zone: 19, receiver: FB}   # touch 1：傳球 7.5
  - {zone: 20, receiver: ST}   # touch 2：傳中 7.5
```

→ `earned: 15.0 / max_points: 15.0`

地點錯（例如 FB 在 `右邊路` 而非 `右路底線`）→ 該項 `place` 20% 拿不到，其餘仍可得 → 總分介於 10–15 之間。

---

## 輸出格式

`scoring_to_dict()` 產生 JSON 結構，供 Web UI 右側「評分」面板與 CLI `--json` 使用：

```json
{
  "max_points": 15,
  "earned": 15.0,
  "ratio": 1.0,
  "items": [
    {
      "name": "傳球",
      "max_points": 7.5,
      "earned": 7.5,
      "criteria": [
        {"label": "傳球人", "matched": true, "earned": 2.25, "max_points": 2.25, "detail": "..."},
        {"label": "邊", "matched": true, ...},
        {"label": "接球點", "matched": true, ...}
      ]
    }
  ]
}
```

---

## 題目覆蓋現況

| 題目 | `scoring:` rubric |
|------|-------------------|
| A001 (`a001.yaml`) | 有（15 分，傳球 + 傳中） |
| T002–T012 | 尚無；需在各題 YAML 補 `scoring:` 才會自動評分 |

`evaluation_points` 文字說明來自 `build_evaluation_points()`，與 rubric 評分獨立；有 rubric 時以 `scoring` 數字為準。

---

## 測試

```bash
python3 -m unittest tactic_translate.test_scoring -v
```

- `test_t001_perfect_score` — 三拍正確 → 15/15
- `test_t001_partial_wrong_place` — 地點錯 → 部分分
- `test_rubric_loads_from_001_yaml` — rubric 解析

---

## 相關原始碼

| 檔案 | 職責 |
|------|------|
| `scoring.py` | rubric 解析、`score_item` / `score_touches` |
| `touches.py` | `build_touches`、邊／結果推斷 |
| `patterns.py` | 戰術 pattern 偵測（影響邊推斷） |
| `zones.py` | 20 區定義、`zone_name()` |
| `zone_map.svg` | 區域示意圖（Zone 編號 + 中文名）；重產：`python -m tactic_translate.plot_zone_map` |
| `translator.py` | `translate_board()` 串接驗證、觸碰軸、評分 |
| `a001.yaml` | 第一題 rubric 範本 |
