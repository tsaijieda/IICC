/* Board-game UI for 解防守題 */

const KIND_LABEL = {
  presser: "逼",
  block: "閘",
  shadow: "影",
  interceptor: "截",
  goalkeeper: "門",
};

let state = null;
let mode = null; // move | dribble | pass | lob | shoot
let moveActorId = null;
let pathPreview = [];
let demoPlaying = false;
let demoHighlight = null; // {x,y} or {id} during demo

const $ = (sel) => document.querySelector(sel);
const boardEl = $("#board");
const logEl = $("#log");
const puzzleList = $("#puzzle-list");

async function api(path, body) {
  const opts = body
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    : {};
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok && data.message) throw new Error(data.message);
  return data;
}

function setPrompt(text) {
  $("#prompt").textContent = text;
}

function appendLogs(logs, message) {
  if (message) {
    const mark = document.createElement("li");
    mark.className = "turn-mark";
    mark.textContent = `— ${message} —`;
    logEl.prepend(mark);
  }
  [...(logs || [])].reverse().forEach((line) => {
    const li = document.createElement("li");
    li.textContent = line;
    logEl.prepend(li);
  });
}

function showModal(title, body) {
  $("#modal-title").textContent = title;
  $("#modal-body").textContent = body;
  $("#modal").classList.remove("hidden");
}

function cellsOnSegment(ax, ay, bx, by) {
  let x0 = ax, y0 = ay;
  const x1 = bx, y1 = by;
  const dx = Math.abs(x1 - x0);
  const dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1;
  const sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  const cells = [];
  for (;;) {
    cells.push([x0, y0]);
    if (x0 === x1 && y0 === y1) break;
    const e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x0 += sx; }
    if (e2 < dx) { err += dx; y0 += sy; }
  }
  return cells;
}

function pieceAt(x, y) {
  const a = state.attackers.find((p) => p.x === x && p.y === y);
  if (a) return { side: "atk", ...a };
  const d = state.defenders.find((p) => p.x === x && p.y === y);
  if (d) return { side: "def", ...d };
  return null;
}

function holder() {
  return state.attackers.find((a) => a.id === state.ball_holder_id);
}

function validTargets() {
  if (!state || state.finished || !mode) return [];
  const h = holder();
  const out = [];

  if (mode === "dribble") {
    if (h.moved) return out;
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        if (dx === 0 && dy === 0) continue;
        const x = h.x + dx, y = h.y + dy;
        if (x < 0 || y < 0 || x >= state.cols || y >= state.rows) continue;
        if (state.attackers.some((a) => a.id !== h.id && a.x === x && a.y === y)) continue;
        if (state.defenders.some((d) => d.x === x && d.y === y)) continue;
        out.push({ x, y, kind: "cell" });
      }
    }
  }

  if (mode === "move") {
    const actors = state.attackers.filter((a) => !a.moved);
    if (!moveActorId) {
      actors.forEach((a) => out.push({ x: a.x, y: a.y, kind: "actor", id: a.id }));
    } else {
      const actor = state.attackers.find((a) => a.id === moveActorId);
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          if (dx === 0 && dy === 0) continue;
          const x = actor.x + dx, y = actor.y + dy;
          if (x < 0 || y < 0 || x >= state.cols || y >= state.rows) continue;
          if (state.attackers.some((a) => a.id !== actor.id && a.x === x && a.y === y)) continue;
          if (state.defenders.some((d) => d.x === x && d.y === y)) continue;
          out.push({ x, y, kind: "cell" });
        }
      }
    }
  }

  if (mode === "pass" || mode === "lob") {
    state.attackers
      .filter((a) => a.id !== state.ball_holder_id)
      .forEach((a) => out.push({ x: a.x, y: a.y, kind: "receiver", id: a.id }));
  }

  if (mode === "shoot") {
    state.goal_cells.forEach(([x, y]) => out.push({ x, y, kind: "goal" }));
  }

  return out;
}

function renderBoard() {
  boardEl.innerHTML = "";
  boardEl.style.gridTemplateColumns = `repeat(${state.cols}, var(--cell))`;
  boardEl.style.gridTemplateRows = `repeat(${state.rows}, var(--cell))`;

  const goals = new Set(state.goal_cells.map(([x, y]) => `${x},${y}`));
  const valids = new Set(validTargets().map((t) => `${t.x},${t.y}`));
  const pathSet = new Set(pathPreview.map(([x, y]) => `${x},${y}`));

  // y high (goal) at top of grid
  for (let y = state.rows - 1; y >= 0; y--) {
    for (let x = 0; x < state.cols; x++) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "cell";
      cell.dataset.x = x;
      cell.dataset.y = y;
      cell.setAttribute("aria-label", `格子 ${x},${y}`);
      if (goals.has(`${x},${y}`)) cell.classList.add("goal");
      if (valids.has(`${x},${y}`)) cell.classList.add("valid");
      if (pathSet.has(`${x},${y}`)) {
        cell.classList.add(mode === "lob" ? "path-lob" : "path-ground");
      }

      const p = pieceAt(x, y);
      if (
        demoHighlight &&
        ((demoHighlight.id && p && p.id === demoHighlight.id) ||
          (demoHighlight.x === x && demoHighlight.y === y))
      ) {
        cell.classList.add("demo-focus");
      }
      if (p) {
        const el = document.createElement("div");
        el.className = `piece ${p.side}`;
        if (p.side === "atk" && p.has_ball) el.classList.add("ball");
        if (p.side === "atk" && p.moved) el.classList.add("moved");
        if (p.side === "atk" && moveActorId === p.id) el.classList.add("selected");
        if (p.side === "def" && p.kind === "goalkeeper") el.classList.add("gk");
        if (p.side === "atk") {
          el.textContent = p.id;
        } else {
          el.textContent = `${KIND_LABEL[p.kind] || "D"}`;
          const role = KIND_LABEL[p.kind] || p.kind || "防守";
          const blurb = p.blurb ? ` — ${p.blurb}` : "";
          el.title = `${p.label} · ${role}${blurb}`;
        }
        cell.appendChild(el);
      }

      cell.addEventListener("click", () => onCellClick(x, y));
      cell.addEventListener("mouseenter", () => onCellHover(x, y));
      cell.addEventListener("mouseleave", () => {
        pathPreview = [];
        applyPathClasses();
      });
      boardEl.appendChild(cell);
    }
  }
}

function applyPathClasses() {
  boardEl.querySelectorAll(".cell").forEach((cell) => {
    cell.classList.remove("path-ground", "path-lob");
    const key = `${cell.dataset.x},${cell.dataset.y}`;
    if (pathPreview.some(([x, y]) => `${x},${y}` === key)) {
      cell.classList.add(mode === "lob" ? "path-lob" : "path-ground");
    }
  });
}

function onCellHover(x, y) {
  if (!mode || !state) return;
  const h = holder();
  if (mode === "pass" || mode === "lob") {
    const recv = state.attackers.find((a) => a.x === x && a.y === y && a.id !== h.id);
    pathPreview = recv ? cellsOnSegment(h.x, h.y, recv.x, recv.y).slice(1, -1) : [];
    applyPathClasses();
  } else if (mode === "shoot") {
    const isGoal = state.goal_cells.some(([gx, gy]) => gx === x && gy === y);
    pathPreview = isGoal ? cellsOnSegment(h.x, h.y, x, y).slice(1) : [];
    applyPathClasses();
  }
}

async function onCellClick(x, y) {
  if (demoPlaying || !mode || state.finished) return;
  const targets = validTargets();
  const hit = targets.find((t) => t.x === x && t.y === y);
  if (!hit) return;

  try {
    if (mode === "move" && hit.kind === "actor") {
      moveActorId = hit.id;
      setPrompt(`已選 ${hit.id}：點選要走到的相鄰格`);
      renderBoard();
      return;
    }

    let payload = { type: mode };
    if (mode === "move") {
      payload.actor_id = moveActorId;
      payload.x = x;
      payload.y = y;
    } else if (mode === "dribble" || mode === "shoot") {
      payload.x = x;
      payload.y = y;
    } else if (mode === "pass" || mode === "lob") {
      payload.target_id = hit.id;
    }

    const res = await api("/api/action", payload);
    state = res.state;
    appendLogs(res.logs, res.message);
    const pending = res.message && !state.finished && !res.goal && !res.turnover
      && (payload.type === "move" || payload.type === "dribble");
    if (pending) {
      moveActorId = null;
      pathPreview = [];
      mode = "move";
      setPrompt(res.message);
    } else {
      clearMode();
    }
    paintHud();
    renderBoard();
    if (state.finished) {
      if (state.won) {
        showModal("進球！", `${state.puzzle.title}\n用了 ${state.turn} 回合，得分 ${state.score}/10`);
      } else {
        showModal("挑戰結束", res.message || "失去球權或回合用盡");
      }
    }
  } catch (err) {
    setPrompt(err.message);
  }
}

function paintHud() {
  $("#title").textContent = `${state.puzzle.id}　${state.puzzle.title}`;
  $("#desc").textContent = state.puzzle.description;
  $("#turn").textContent = `${state.turn}/${state.max_turns}`;
  const h = holder();
  $("#holder").textContent = h ? `${h.id}` : "—";
  $("#score").textContent = state.finished && state.won ? `${state.score}` : "—";

  document.querySelectorAll(".puzzle-list button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.id === state.puzzle.id);
  });

  document.querySelectorAll(".action-row .act[data-act]").forEach((btn) => {
    const act = btn.dataset.act;
    const tools = (state.puzzle && state.puzzle.tools) || {};
    const moved = (state.moved_ids || []).length > 0;
    const afterCarry = !!state.after_carry;
    const holder = state.attackers && state.attackers.find((a) => a.id === state.ball_holder_id);
    const minShootY = state.min_shoot_y != null ? state.min_shoot_y : 4;
    const tooFar = holder && holder.y < minShootY;
    let allowed =
      !demoPlaying &&
      (act === "shoot" || act === "end" || tools[act] !== false);
    // After off-ball runs: pass/lob/end/move OK; no shoot or dribble same turn.
    if (moved && (act === "shoot" || act === "dribble")) allowed = false;
    // After a carry: pass/end/move OK; no shoot or re-dribble same turn.
    if (afterCarry && (act === "shoot" || act === "dribble")) {
      allowed = false;
    }
    if (act === "shoot" && tooFar) allowed = false;
    btn.disabled = !!state.finished || !allowed || demoPlaying;
    btn.classList.toggle("locked", !allowed);
    btn.classList.toggle("active", btn.dataset.act === mode);
    if (!allowed && mode === act) mode = null;
  });
  const endBtn = $("#btn-end");
  if (endBtn) endBtn.disabled = !!state.finished || demoPlaying;
  const demoBtn = $("#btn-demo");
  if (demoBtn) demoBtn.disabled = demoPlaying;

  const hint = $("#tools-hint");
  if (hint && state.puzzle && state.puzzle.tools) {
    const t = state.puzzle.tools;
    const on = [];
    if (t.move) on.push("無球跑");
    if (t.dribble) on.push("盤帶");
    if (t.pass) on.push("地滾");
    if (t.lob) on.push("高空");
    on.push("射門");
    const moved = (state.moved_ids || []).length > 0;
    const afterCarry = !!state.after_carry;
    if (afterCarry) {
      hint.textContent = "已盤帶：可繼續跑位或傳球；防守等結束回合／傳球後才動；不能射門／再盤帶";
    } else if (moved) {
      hint.textContent = "本回合已跑位：可繼續移動或傳球；射門／盤帶須先結束回合";
    } else {
      const minY = state.min_shoot_y != null ? state.min_shoot_y : 4;
      hint.textContent = `本關手段：${on.join(" · ")} · 射門須 y≥${minY}（灰鈕＝鎖死）`;
    }
  }
}

function clearMode() {
  mode = null;
  moveActorId = null;
  pathPreview = [];
  const moved = (state.moved_ids || []).length;
  const afterCarry = !!state.after_carry;
  setPrompt(
    state.finished
      ? "本關已結束，可重開或選其他關卡。"
      : afterCarry
        ? "已盤帶 — 可繼續移動其他球員或傳球；防守尚未動。不能射門／再盤帶。"
        : moved
          ? `本回合已跑位 ${moved} 人 — 可繼續移動或傳球；不能射門／盤帶，或結束回合。`
          : "先跑位拉扯防線；傳球後防守者會跟上。也可直接射門。"
  );
}

function selectMode(next) {
  if (state.finished) return;
  mode = next;
  moveActorId = null;
  pathPreview = [];
  const prompts = {
    move: "點尚未移動的進攻球員，再點相鄰格（每人每回合 1 格；持球＝盤帶）",
    dribble: "點選持球者相鄰格盤帶（本回合限一次）",
    pass: "點接球隊友（地滾）。傳球後防守者會移動——用來拉扯防線。",
    lob: "點接球隊友（高空）。傳球後防守者會移動。",
    shoot: "須推進到前場（y≥4）才能射。點球門三格。",
  };
  setPrompt(prompts[next]);
  paintHud();
  renderBoard();
}

async function endTurn() {
  if (state.finished) return;
  try {
    const res = await api("/api/action", { type: "end" });
    state = res.state;
    appendLogs(res.logs, res.message);
    clearMode();
    paintHud();
    renderBoard();
    if (state.finished) {
      showModal("挑戰結束", res.message || "失去球權或回合用盡");
    }
  } catch (err) {
    setPrompt(err.message);
  }
}

async function loadPuzzle(id) {
  if (demoPlaying) return;
  const res = await api("/api/new", { puzzle_id: id });
  state = res.state;
  logEl.innerHTML = "";
  appendLogs([], `開始 ${state.puzzle.id}`);
  clearMode();
  paintHud();
  renderBoard();
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function demoFocusForStep(step) {
  if (step.target_id) return { id: step.target_id };
  if (step.actor_id) return { id: step.actor_id };
  if (step.x != null && step.y != null) return { x: step.x, y: step.y };
  return null;
}

function previewPathForStep(step) {
  const h = holder();
  if (!h) return [];
  if (step.type === "pass" || step.type === "lob") {
    const recv = state.attackers.find((a) => a.id === step.target_id);
    return recv ? cellsOnSegment(h.x, h.y, recv.x, recv.y).slice(1, -1) : [];
  }
  if (step.type === "shoot" && step.x != null) {
    return cellsOnSegment(h.x, h.y, step.x, step.y).slice(1);
  }
  return [];
}

async function playSolutionDemo() {
  if (!state || demoPlaying) return;
  demoPlaying = true;
  document.body.classList.add("demo-playing");
  setPrompt("正解示範播放中…");

  try {
    const pack = await api("/api/solution", { puzzle_id: state.puzzle.id });
    if (!pack.ok) throw new Error(pack.message || "無法載入正解");
    const frames = pack.frames;
    if (!frames?.length) throw new Error("正解步驟為空");

    state = pack.state;
    logEl.innerHTML = "";
    appendLogs([], `正解示範 · ${pack.puzzle_id}`);
    clearMode();
    paintHud();
    renderBoard();
    await sleep(500);

    for (const frame of frames) {
      demoHighlight = demoFocusForStep(frame);
      pathPreview = previewPathForStep(frame);
      const prevMode = mode;
      mode = frame.type === "lob" ? "lob" : frame.type === "pass" ? "pass" : mode;
      setPrompt(frame.label);
      appendLogs([], frame.label);
      paintHud();
      renderBoard();
      await sleep(900);

      // Server already applied this step — just show the resulting board.
      state = frame.state;
      appendLogs(frame.logs, frame.message);
      demoHighlight = null;
      pathPreview = [];
      mode = prevMode;
      paintHud();
      renderBoard();
      await sleep(700);

      if (!frame.ok || (frame.turnover && !frame.goal)) {
        throw new Error(frame.message || "示範步驟失敗");
      }
      if (state.finished) break;
    }

    if (pack.won || state.won) {
      showModal(
        "正解示範完成",
        `${state.puzzle.title}\n\n這就是本關要學的解法。按「重開本關」自己再試一次。`
      );
    } else {
      showModal("示範中斷", "示範未能完成進球，請重開本關再試。");
    }
  } catch (err) {
    setPrompt("示範失敗：" + err.message);
    showModal("示範失敗", err.message || "未知錯誤");
  } finally {
    demoPlaying = false;
    demoHighlight = null;
    pathPreview = [];
    document.body.classList.remove("demo-playing");
    clearMode();
    paintHud();
    renderBoard();
  }
}

async function init() {
  const list = await api("/api/puzzles");
  puzzleList.innerHTML = "";
  const groups = list.categories?.length
    ? list.categories
    : [{ id: "all", label: "關卡", puzzles: list.puzzles || [] }];

  groups.forEach((cat) => {
    if (!cat.puzzles?.length) return;
    const heading = document.createElement("p");
    heading.className = "puzzle-cat";
    heading.textContent = cat.label;
    puzzleList.appendChild(heading);

    cat.puzzles.forEach((p) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.dataset.id = p.id;
      btn.innerHTML = `<span class="pid">${p.id}</span><span class="ptitle">${p.title}</span>`;
      btn.addEventListener("click", () => loadPuzzle(p.id));
      puzzleList.appendChild(btn);
    });
  });

  document.querySelectorAll(".action-row .act[data-act]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (demoPlaying) return;
      selectMode(btn.dataset.act);
    });
  });
  $("#btn-end").addEventListener("click", () => {
    if (!demoPlaying) endTurn();
  });
  $("#btn-reset").addEventListener("click", () => {
    if (!demoPlaying) loadPuzzle(state.puzzle.id);
  });
  $("#btn-hint").addEventListener("click", () => {
    if (!demoPlaying) showModal("提示", state.puzzle.tip);
  });
  $("#btn-demo").addEventListener("click", () => playSolutionDemo());
  $("#modal-ok").addEventListener("click", () => {
    $("#modal").classList.add("hidden");
  });
  $("#modal").addEventListener("click", (e) => {
    if (e.target.id === "modal") $("#modal").classList.add("hidden");
  });

  await loadPuzzle("D1");
}

init().catch((err) => {
  setPrompt("無法連線伺服器：" + err.message);
});
