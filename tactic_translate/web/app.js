/** Tactical board → 戰術語言 UI（預設：只記傳球點） */

/** 場地名稱（與 tactic_translate/zones.py 同步） */
const ZONE_NAMES = {
  1: "後場左角",
  2: "後場禁區",
  3: "後場右角",
  4: "左邊路（後段）",
  5: "左邊路（中段）",
  6: "左肋深處",
  7: "後場中路",
  8: "右肋深處",
  9: "右邊路（後段）",
  10: "右邊路（中段）",
  11: "左邊路",
  12: "左邊路（前段）",
  13: "左肋",
  14: "弧頂前緣",
  15: "右肋",
  16: "右路中路",
  17: "右邊路",
  18: "左路底線",
  19: "右路底線",
  20: "禁區中央",
};

function buildDefaultZoneRects() {
  const PW = 68;
  const PL = 105;
  const PAW = 40.32;
  const PAD = 16.5;
  const WG = (PW - PAW) / 2;
  const CW = PAW / 3;
  const HM = (PL - 2 * PAD) / 2;
  const WH = HM / 2;
  const cx = WG;
  const half = PAD + HM;
  const bottom = PL - PAD;
  const pct = (zone, x, y, w, h) => ({
    zone,
    x: Math.round((x / PW) * 10000) / 100,
    y: Math.round((y / PL) * 10000) / 100,
    w: Math.round((w / PW) * 10000) / 100,
    h: Math.round((h / PL) * 10000) / 100,
  });
  return [
    pct(18, 0, 0, WG, PAD),
    pct(20, WG, 0, PAW, PAD),
    pct(19, WG + PAW, 0, WG, PAD),
    pct(12, 0, PAD, WG, WH),
    pct(13, cx, PAD, CW, HM),
    pct(14, cx + CW, PAD, CW, HM),
    pct(15, cx + 2 * CW, PAD, CW, HM),
    pct(17, WG + PAW, PAD, WG, WH),
    pct(11, 0, PAD + WH, WG, WH),
    pct(16, WG + PAW, PAD + WH, WG, WH),
    pct(5, 0, half, WG, WH),
    pct(6, cx, half, CW, HM),
    pct(7, cx + CW, half, CW, HM),
    pct(8, cx + 2 * CW, half, CW, HM),
    pct(10, WG + PAW, half, WG, WH),
    pct(4, 0, half + WH, WG, WH),
    pct(9, WG + PAW, half + WH, WG, WH),
    pct(1, 0, bottom, WG, PAD),
    pct(2, WG, bottom, PAW, PAD),
    pct(3, WG + PAW, bottom, WG, PAD),
  ];
}

const state = {
  layout: [],
  cells: [],
  gridRows: 6,
  gridCols: 5,
  pitchAspect: 105 / 68,
  zoneRects: buildDefaultZoneRects(),
  zoneNames: {},
  playId: "A001",
  title: "",
  mode: "pass_points",
  gradingMode: "draw_runs",
  frameIndex: 0,
  frames: [],
  selectedPlayerId: null,
  lastResult: null,
};

let translateTimer = null;

function scheduleTranslate() {
  if (!isPassPointsMode()) return;
  clearTimeout(translateTimer);
  translateTimer = setTimeout(() => {
    translate().catch((err) => {
      console.error(err);
      const flag = document.getElementById("valid-flag");
      if (flag) {
        flag.textContent = `轉譯失敗：${err.message || err}`;
        flag.className = "valid bad";
      }
    });
  }, 250);
}

function touchComplete(f) {
  return f.ball_zone != null && String(f.receiver || "").trim();
}

function recordedFrames() {
  return state.frames.filter((f) => touchComplete(f));
}

function canTranslate() {
  return isPassPointsMode() && recordedFrames().length >= 2;
}

function emptyFrame(index = 0) {
  const n = index + 1;
  return {
    receiver: `T${n}`,
    ball_zone: null,
    offside_line_depth: null,
    players: [],
  };
}

function isPassPointsMode() {
  return state.mode === "pass_points";
}

function isDrawRunsMode() {
  return state.gradingMode === "draw_runs";
}

function gradingModeLabel() {
  return isDrawRunsMode() ? "畫跑位" : "跑戰術";
}

function gradingModeMax() {
  return isDrawRunsMode() ? 15 : 30;
}

function isAddingTouch() {
  return state.frameIndex >= state.frames.length;
}

function currentFrame() {
  if (isAddingTouch()) return null;
  return state.frames[state.frameIndex];
}

function ensureFrames() {
  state.frameIndex = state.frames.length;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function placeName(zid) {
  if (zid == null) return "?";
  const key = String(zid);
  const fromApi = state.zoneNames[key];
  if (fromApi && fromApi !== key && !/^\d+$/.test(fromApi)) return fromApi;
  return ZONE_NAMES[zid] || ZONE_NAMES[Number(key)] || `區域${zid}`;
}

function buildPassPointsFromFrames() {
  return recordedFrames().map((f) => ({
    zone: f.ball_zone,
    place: placeName(f.ball_zone),
    receiver: f.receiver.trim(),
  }));
}

function buildBoardPayload() {
  const passPoints = isPassPointsMode();
  return {
    play_id: document.getElementById("play-id").value || state.playId,
    title: document.getElementById("play-title").value || state.title,
    mode: state.mode,
    grading_mode: state.gradingMode,
    frames: (passPoints ? recordedFrames() : state.frames).map((f, i) => {
      if (passPoints) {
        return {
          zone: f.ball_zone,
          receiver: f.receiver.trim(),
          offside_line_depth: f.offside_line_depth ?? null,
        };
      }
      return {
        receiver: f.receiver,
        ball_zone: f.ball_zone,
        offside_line_depth: f.offside_line_depth ?? null,
        players: f.players.map((p) => ({ id: p.id, role: p.role, zone: p.zone })),
      };
    }),
  };
}

function appendZoneTokens(cell, zid) {
  const frame = currentFrame();
  if (isPassPointsMode()) {
    if (frame && frame.ball_zone === zid) {
      const tok = document.createElement("span");
      tok.className = "token ball-touch";
      tok.textContent = (frame.receiver || "?").slice(0, 4);
      tok.title = `${frame.receiver || "?"} @ ${placeName(zid)}`;
      cell.appendChild(tok);
    }
    for (let i = 0; i < state.frames.length; i++) {
      if (!isAddingTouch() && i === state.frameIndex) continue;
      const f = state.frames[i];
      if (f.ball_zone === zid) {
        const ghost = document.createElement("span");
        ghost.className = "token ghost-touch";
        ghost.textContent = (f.receiver || `T${i + 1}`).slice(0, 4);
        ghost.title = `${f.receiver || "?"} @ ${placeName(zid)}`;
        cell.appendChild(ghost);
      }
    }
  } else if (frame) {
    const here = frame.players.filter((p) => p.zone === zid);
    for (const p of here) {
      const tok = document.createElement("span");
      tok.className = "token atk";
      if (p.id === frame.receiver) tok.classList.add("ball-holder");
      tok.textContent = p.id.slice(0, 2);
      tok.title = `${p.role} (${p.id})`;
      cell.appendChild(tok);
    }
  }
}

function renderBoard() {
  const board = document.getElementById("board");
  board.style.display = "block";
  board.style.gridTemplateColumns = "";
  board.style.gridTemplateRows = "";

  board.querySelectorAll(".zone").forEach((el) => el.remove());

  for (const spec of state.zoneRects) {
    const zid = spec.zone;
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "zone";
    if (zid === 2 || zid === 20) cell.classList.add("penalty");
    if (zid === 20) cell.classList.add("goal-row", "box");

    cell.style.left = `${spec.x}%`;
    cell.style.top = `${spec.y}%`;
    cell.style.width = `${spec.w}%`;
    cell.style.height = `${spec.h}%`;

    const num = document.createElement("span");
    num.className = "znum";
    num.textContent = zid;
    cell.appendChild(num);

    const label = document.createElement("span");
    label.className = "zid";
    label.textContent = placeName(zid);
    cell.title = `${zid} · ${placeName(zid)}`;
    cell.appendChild(label);

    appendZoneTokens(cell, zid);
    cell.addEventListener("click", () => onZoneClick(zid));
    board.appendChild(cell);
  }
}

function fallbackCellsFromLayout() {
  const out = [];
  state.layout.forEach((row, r) => {
    row.forEach((zid, c) => {
      if (zid == null) return;
      const prev = out.find((x) => x.zone === zid);
      if (prev) return;
      out.push({ zone: zid, row: r + 1, col: c + 1, row_span: 1, col_span: 1 });
    });
  });
  return out;
}

function renderPlayers() {
  const section = document.getElementById("roster-section");
  section.hidden = isPassPointsMode();

  const ul = document.getElementById("players");
  const frame = currentFrame();
  ul.innerHTML = "";
  if (!frame) return;

  frame.players.forEach((p) => {
    const li = document.createElement("li");
    li.className = "player-row" + (state.selectedPlayerId === p.id ? " selected" : "");

    const idIn = document.createElement("input");
    idIn.value = p.id;
    idIn.addEventListener("change", () => {
      if (frame.receiver === p.id) frame.receiver = idIn.value;
      p.id = idIn.value;
      renderAll();
    });

    const roleIn = document.createElement("input");
    roleIn.value = p.role;
    roleIn.addEventListener("change", () => { p.role = roleIn.value; });

    const zoneTag = document.createElement("span");
    zoneTag.className = "zone-tag";
    zoneTag.textContent = p.zone != null ? `zone ${p.zone}` : "未放置";

    const recvBtn = document.createElement("button");
    recvBtn.type = "button";
    recvBtn.className = "recv" + (frame.receiver === p.id ? " active" : "");
    recvBtn.textContent = "接球";
    recvBtn.addEventListener("click", () => {
      frame.receiver = p.id;
      frame.ball_zone = p.zone;
      renderAll();
    });

    const delBtn = document.createElement("button");
    delBtn.type = "button";
    delBtn.className = "del";
    delBtn.textContent = "刪";
    delBtn.addEventListener("click", () => {
      frame.players = frame.players.filter((x) => x.id !== p.id);
      if (frame.receiver === p.id) {
        frame.receiver = "";
        frame.ball_zone = null;
      }
      if (state.selectedPlayerId === p.id) state.selectedPlayerId = null;
      renderAll();
    });

    li.addEventListener("click", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") return;
      state.selectedPlayerId = p.id;
      renderPlayers();
    });

    li.append(idIn, roleIn, zoneTag, recvBtn, delBtn);
    ul.appendChild(li);
  });
}

function frameLabel(f, i) {
  const recv = f.receiver || `T${i + 1}`;
  if (f.ball_zone == null) return `${i + 1}. ${recv}`;
  return `${i + 1}. ${recv} · ${placeName(f.ball_zone)}`;
}

function renderFrames() {
  const wrap = document.getElementById("frames");
  wrap.innerHTML = "";
  state.frames.forEach((f, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = i === state.frameIndex ? "active" : "";
    btn.textContent = frameLabel(f, i);
    btn.addEventListener("click", () => {
      state.frameIndex = i;
      syncFrameControls();
      renderAll();
    });
    wrap.appendChild(btn);
  });

  const addBtn = document.createElement("button");
  addBtn.type = "button";
  addBtn.className = isAddingTouch() ? "active" : "";
  addBtn.textContent = `＋ 第 ${state.frames.length + 1} 拍`;
  addBtn.addEventListener("click", () => {
    state.frameIndex = state.frames.length;
    syncFrameControls();
    renderAll();
  });
  wrap.appendChild(addBtn);

  const title = document.getElementById("frame-title");
  if (isPassPointsMode()) {
    if (isAddingTouch()) {
      title.textContent = `新增第 ${state.frames.length + 1} 拍`;
    } else {
      const f = currentFrame();
      const placeHint = f?.ball_zone != null ? ` · ${placeName(f.ball_zone)}` : "";
      title.textContent = `編輯第 ${state.frameIndex + 1} 拍${placeHint}`;
    }
  } else {
    title.textContent = `接球時刻 ${state.frameIndex + 1}`;
  }
}

function syncFrameControls() {
  const f = currentFrame();
  const receiverIn = document.getElementById("touch-receiver");
  const editor = document.getElementById("touch-editor");

  if (isPassPointsMode()) {
    editor.hidden = false;
    receiverIn.value = f ? f.receiver || "" : "";
    receiverIn.oninput = () => {
      if (f) {
        f.receiver = receiverIn.value.trim();
        renderFrames();
        renderBoard();
        renderTouchRecord();
        scheduleTranslate();
      }
    };
    receiverIn.onchange = receiverIn.oninput;
  } else {
    editor.hidden = true;
  }

  const sel = document.getElementById("offside-depth");
  if (!sel) return;
  sel.value = f?.offside_line_depth ?? "";
  sel.onchange = () => {
    if (!f) return;
    const v = sel.value;
    f.offside_line_depth = v === "" ? null : Number(v);
  };
}

function syncModeUi() {
  const passPoints = isPassPointsMode();
  document.getElementById("mode-draw").classList.toggle("active", isDrawRunsMode());
  document.getElementById("mode-run").classList.toggle("active", !isDrawRunsMode());
  document.getElementById("frame-hint").textContent = passPoints
    ? `評分模式：${gradingModeLabel()}（滿分 ${gradingModeMax()}）。填接球人 → 點球場記錄每一拍。`
    : "點選球員 → 再點 zone 放置；點「接球」設為該拍持球者。";
  const rec = document.getElementById("touch-record-section");
  if (rec) rec.hidden = !passPoints;
}

function onZoneClick(zid) {
  if (isPassPointsMode()) {
    const receiverIn = document.getElementById("touch-receiver");
    const receiver = receiverIn.value.trim();

    if (!isAddingTouch()) {
      const frame = currentFrame();
      frame.ball_zone = zid;
      if (receiver) frame.receiver = receiver;
      state.frameIndex = state.frames.length;
      receiverIn.value = "";
    } else {
      if (!receiver) {
        receiverIn.focus();
        return;
      }
      state.frames.push({
        receiver,
        ball_zone: zid,
        offside_line_depth: null,
        players: [],
      });
      state.frameIndex = state.frames.length;
      receiverIn.value = "";
    }

    syncFrameControls();
    renderAll();
    scheduleTranslate();
    return;
  }

  const frame = currentFrame();
  if (!frame) return;

  if (state.selectedPlayerId) {
    const p = frame.players.find((x) => x.id === state.selectedPlayerId);
    if (p) {
      p.zone = zid;
      if (frame.receiver === p.id) frame.ball_zone = zid;
    }
  } else {
    const occupant = frame.players.find((p) => p.zone === zid);
    if (occupant) {
      frame.receiver = occupant.id;
      frame.ball_zone = zid;
      state.selectedPlayerId = occupant.id;
    }
  }
  renderAll();
}

function renderTouchRecord() {
  const list = document.getElementById("touch-record");
  if (!list) return;
  list.innerHTML = "";

  const touches = state.lastResult?.valid ? state.lastResult.touches : null;

  state.frames.forEach((f, i) => {
    const li = document.createElement("li");
    li.className = i === state.frameIndex ? "active" : "";
    const recv = (f.receiver || `T${i + 1}`).trim();
    const place = f.ball_zone != null ? placeName(f.ball_zone) : null;
    const t = touches?.[i];

    if (!place) {
      li.classList.add("incomplete");
      li.innerHTML = `
        <div class="rec-main">${i + 1}. ${recv} · 尚未選位置</div>
        <div class="rec-sub">點球場上的格子和這一拍對應的位置</div>
      `;
    } else {
      const passLine =
        t && i > 0 && t.passer
          ? [t.passer, t.pass_action, t.outcome].filter(Boolean).join(" · ")
          : i === 0
            ? "首拍"
            : t
              ? ""
              : `已記錄：${recv} @ ${place}`;
      li.innerHTML = `
        <div class="rec-main">${i + 1}. ${recv} 在 ${place} 接球</div>
        ${passLine ? `<div class="rec-sub">${passLine}</div>` : ""}
        ${t?.narrative ? `<div class="rec-sub">${t.narrative}</div>` : ""}
      `;
    }

    li.addEventListener("click", () => {
      state.frameIndex = i;
      syncFrameControls();
      renderAll();
    });
    list.appendChild(li);
  });
}

function renderOutput(result) {
  const flag = document.getElementById("valid-flag");
  if (!result) {
    flag.textContent = "—";
    flag.className = "valid";
    document.getElementById("out-desc").textContent = "（按「轉譯戰術」）";
    document.getElementById("out-evals").innerHTML = "";
    document.getElementById("out-touches").innerHTML = "";
    document.getElementById("out-score").textContent = "（戰術 ID 對應題目時自動評分）";
    document.getElementById("out-scoring").innerHTML = "";
    return;
  }
  if (result.valid) {
    flag.textContent = "戰術板有效";
    flag.className = "valid ok";
  } else {
    flag.textContent = result.invalid_reason || "無效";
    flag.className = "valid bad";
  }
  document.getElementById("out-desc").textContent = result.description || "—";

  const scoreEl = document.getElementById("out-score");
  const scoreList = document.getElementById("out-scoring");
  scoreList.innerHTML = "";
  if (result.scoring) {
    const s = result.scoring;
    const modeLabel = s.grading_mode_label || gradingModeLabel();
    scoreEl.textContent = `${modeLabel}：${s.earned} / ${s.max_points} 分（${Math.round(s.ratio * 100)}%）`;
    for (const item of s.items || []) {
      const li = document.createElement("li");
      const crit = (item.criteria || [])
        .map(
          (c) =>
            `<div class="scoring-criteria ${c.matched ? "ok" : "bad"}">${c.label} ${
              c.earned
            }/${c.max_points} — ${c.detail}</div>`
        )
        .join("");
      li.innerHTML = `<div class="scoring-item">${item.name}：${item.earned} / ${item.max_points}</div>${crit}`;
      scoreList.appendChild(li);
    }
  } else {
    scoreEl.textContent = "（此戰術 ID 尚無評分標準，請填 A001 測試）";
  }

  const evals = document.getElementById("out-evals");
  evals.innerHTML = "";
  for (const [k, v] of Object.entries(result.evaluation_points || {})) {
    const li = document.createElement("li");
    li.innerHTML = `<strong>${k}</strong>${v}`;
    evals.appendChild(li);
  }

  const touchList = document.getElementById("out-touches");
  touchList.innerHTML = "";
  for (const t of result.touches || []) {
    const li = document.createElement("li");
    const meta = [
      `時刻 ${t.time || t.index + 1}`,
      t.receiver,
      `@ ${t.place}`,
      t.passer ? `${t.passer} →` : null,
      t.pass_action,
      t.outcome,
    ]
      .filter(Boolean)
      .join(" · ");
    li.innerHTML = `
      <div class="interval-meta">${meta}</div>
      <div class="touch-narrative">${t.narrative || ""}</div>
    `;
    touchList.appendChild(li);
  }
}

function renderAll() {
  syncModeUi();
  renderFrames();
  renderBoard();
  renderPlayers();
  renderTouchRecord();
}

async function translate() {
  renderTouchRecord();
  if (!canTranslate()) {
    return null;
  }
  const payload = buildBoardPayload();
  const result = await api("/api/translate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.lastResult = result;
  renderOutput(result);
  renderTouchRecord();
  return result;
}

function loadBoardData(data) {
  state.playId = data.play_id || "";
  state.title = data.title || "";
  document.getElementById("play-id").value = state.playId;
  document.getElementById("play-title").value = state.title;

  const rawFrames = data.frames || data.pass_points || [];
  const hasPlayers = rawFrames.some((f) => (f.players || []).length);
  state.mode = data.mode || data.scoring_mode || (hasPlayers ? "full" : "pass_points");
  state.gradingMode = data.grading_mode || "draw_runs";

  state.frames = rawFrames.map((f, i) => ({
    receiver: f.receiver || f.label || `T${i + 1}`,
    ball_zone: f.ball_zone ?? f.zone ?? null,
    offside_line_depth: f.offside_line_depth ?? null,
    players: (f.players || []).map((p) => ({
      id: p.id,
      role: p.role || p.id,
      zone: p.zone,
    })),
  }));
  state.frameIndex = state.frames.length;
  state.selectedPlayerId = null;
  state.lastResult = null;
  syncFrameControls();
  renderAll();
  renderOutput(null);
  scheduleTranslate();
}

async function init() {
  const zones = await api("/api/zones");
  state.layout = zones.layout;
  state.cells = (zones.cells || []).map((c) => ({
    zone: c.zone,
    row: c.row,
    col: c.col,
    row_span: c.row_span || 1,
    col_span: c.col_span || 1,
  }));
  state.gridRows = zones.rows || 6;
  state.gridCols = zones.cols || 5;
  state.pitchAspect = zones.pitch_aspect || state.pitchAspect;
  state.zoneRects = zones.zone_rects?.length ? zones.zone_rects : buildDefaultZoneRects();
  document.documentElement.style.setProperty(
    "--pitch-aspect",
    String(state.pitchAspect)
  );
  state.zoneNames = Object.fromEntries(
    Object.entries(zones.zones || {}).map(([k, v]) => [k, v.name || k])
  );

  ensureFrames();
  document.getElementById("play-id").value = state.playId;
  syncFrameControls();
  renderAll();

  document.getElementById("mode-draw").addEventListener("click", () => {
    state.gradingMode = "draw_runs";
    state.mode = "pass_points";
    renderAll();
    scheduleTranslate();
  });

  document.getElementById("mode-run").addEventListener("click", () => {
    state.gradingMode = "run_tactic";
    state.mode = "pass_points";
    renderAll();
    scheduleTranslate();
  });

  const ex = await api("/api/examples");
  const wrap = document.getElementById("examples");
  for (const item of ex.examples) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = item.id.replace(/_/g, " ");
    btn.addEventListener("click", async () => {
      const data = await api(`/api/examples/${item.id}`);
      loadBoardData(data);
    });
    wrap.appendChild(btn);
  }

  document.getElementById("btn-add-frame").addEventListener("click", () => {
    if (isPassPointsMode()) {
      state.frameIndex = state.frames.length;
      syncFrameControls();
      renderAll();
      document.getElementById("touch-receiver")?.focus();
      return;
    }
    const i = state.frames.length;
    const prev = state.frames[state.frames.length - 1] || emptyFrame(0);
    const dup = {
      receiver: prev.receiver,
      ball_zone: prev.ball_zone,
      offside_line_depth: prev.offside_line_depth,
      players: prev.players.map((p) => ({ ...p })),
    };
    state.frames.push(dup);
    state.frameIndex = state.frames.length - 1;
    syncFrameControls();
    renderAll();
    scheduleTranslate();
  });

  document.getElementById("btn-add-player").addEventListener("click", () => {
    const frame = currentFrame();
    const n = frame.players.length + 1;
    const id = `P${n}`;
    frame.players.push({ id, role: "球員", zone: 14 });
    state.selectedPlayerId = id;
    renderAll();
  });

  document.getElementById("btn-translate").addEventListener("click", () => translate().catch(alert));

  document.getElementById("btn-export").addEventListener("click", async () => {
    const payload = buildBoardPayload();
    const inputPoints = buildPassPointsFromFrames();
    if (isPassPointsMode() && inputPoints.length < 2) {
      alert("請至少完成 2 拍，且每拍都選好位置與接球人");
      return;
    }

    let r = state.lastResult;
    if (isPassPointsMode() && canTranslate() && (!r?.valid || !r?.pass_points)) {
      r = await translate();
    }

    const lines = [
      `play_id: "${payload.play_id}"`,
      `title: "${payload.title}"`,
      `mode: ${payload.mode}`,
    ];

    if (isPassPointsMode()) {
      lines.push("pass_points:");
      const points = r?.pass_points || inputPoints;
      lines.push(
        ...points.map((f) => {
          const bits = [
            `zone: ${f.zone}`,
            `place: ${f.place}`,
            `receiver: ${f.receiver}`,
          ];
          if (f.passer) bits.push(`passer: ${f.passer}`);
          if (f.pass_action) bits.push(`pass_action: ${f.pass_action}`);
          if (f.outcome) bits.push(`outcome: ${f.outcome}`);
          return `  - {${bits.join(", ")}}`;
        })
      );
      if (r?.description) {
        lines.push(`description: "${r.description}"`);
        lines.push("evaluation_points:");
        lines.push(
          ...Object.entries(r.evaluation_points || {}).map(
            ([k, v]) => `  ${k}: "${v}"`
          )
        );
      }
    } else {
      lines.push(
        ...payload.frames.flatMap((f) => [
          `  - receiver: ${f.receiver}`,
          `    ball_zone: ${f.ball_zone}`,
          ...(f.offside_line_depth != null
            ? [`    offside_line_depth: ${f.offside_line_depth}`]
            : []),
          "    players:",
          ...f.players.map(
            (p) => `      - {id: ${p.id}, role: ${p.role}, zone: ${p.zone}}`
          ),
        ])
      );
    }
    const yaml = lines.join("\n");
    navigator.clipboard.writeText(yaml).then(
      () => alert("已複製 YAML 到剪貼簿"),
      () => prompt("複製以下內容：", yaml)
    );
  });

  // 不預載範例，從空白 2 拍開始
}

init().catch((e) => {
  console.error(e);
  alert("無法連線後端，請執行: python play_translate.py");
});
