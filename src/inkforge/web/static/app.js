/* InkForge Editorial Studio Client */

const state = {
  genres: [],
  presets: [],
  settings: null,
  projects: [],
  currentProject: null,
  chapters: [],
  currentChapter: null,
  activeView: "manuscript", // manuscript | bible | tool
  sheetMode: "markup", // markup | edit | diff
  selectedNewGenre: "suspense",
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function esc(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function showToast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.add("hidden"), 3400);
}

function setBusy(busy, text = "正在处理中…") {
  const bar = $("#busy-bar");
  $("#busy-text").textContent = text;
  bar.classList.toggle("hidden", !busy);
}

async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `请求失败 (${res.status})`);
  }
  return data;
}

function genreById(id) {
  return state.genres.find((g) => g.id === id) || { id, name: id, tagline: "" };
}

/* ---------- Bootstrap ---------- */
async function init() {
  bindEvents();
  try {
    const [gRes, sRes, pRes] = await Promise.all([
      api("/api/genres"),
      api("/api/settings"),
      api("/api/projects"),
    ]);
    state.genres = gRes.genres || [];
    state.presets = sRes.presets || [];
    state.settings = sRes.current;
    state.projects = pRes.projects || [];

    renderSettingsBadge();
    renderGenrePickers();
    renderProjectSelect();

    if (state.projects.length > 0) {
      await selectProject(state.projects[0].id);
    } else {
      renderWorkspaceVisibility();
    }
  } catch (err) {
    showToast(`初始化失败：${err.message}`, true);
  }
}

/* ---------- Rendering: Topbar & Genres ---------- */
function renderSettingsBadge() {
  const cur = state.settings || { provider: "demo", model: "" };
  const preset = state.presets.find((p) => p.id === cur.provider);
  const label = preset ? `${preset.label.split("（")[0]}` : cur.provider;
  $("#provider-label").textContent = `${label} · ${cur.model}`;
}

function renderGenrePickers() {
  const strip = $("#empty-genre-strip");
  strip.innerHTML = state.genres
    .map((g) => `<span class="genre-chip">${esc(g.name)}</span>`)
    .join("");

  const toolSel = $("#tool-genre-select");
  toolSel.innerHTML = state.genres
    .map((g) => `<option value="${esc(g.id)}">${esc(g.name)}</option>`)
    .join("");

  const grid = $("#modal-genre-grid");
  grid.innerHTML = state.genres
    .map(
      (g) => `
      <button type="button" class="genre-option ${g.id === state.selectedNewGenre ? "selected" : ""}" data-genre="${esc(g.id)}">
        <strong>${esc(g.name)}</strong>
        <span>${esc(g.en_name)}</span>
      </button>`
    )
    .join("");

  grid.querySelectorAll(".genre-option").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.selectedNewGenre = btn.dataset.genre;
      grid.querySelectorAll(".genre-option").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      const bp = genreById(state.selectedNewGenre);
      if (bp.default_words_per_chapter) {
        $("#new-words").value = bp.default_words_per_chapter;
      }
    });
  });

  const providerSel = $("#set-provider");
  providerSel.innerHTML = state.presets
    .map((p) => `<option value="${esc(p.id)}">${esc(p.label)}</option>`)
    .join("");
}

/* ---------- Rendering: Projects & Chapters ---------- */
function renderProjectSelect() {
  const sel = $("#project-select");
  if (state.projects.length === 0) {
    sel.innerHTML = `<option value="">暂无小说项目</option>`;
    $("#btn-delete-project").classList.add("hidden");
    $("#project-meta").innerHTML = "";
    $("#chapter-list").innerHTML = `<li class="muted-note">请先新建一部小说</li>`;
    return;
  }

  $("#btn-delete-project").classList.remove("hidden");
  sel.innerHTML = state.projects
    .map(
      (p) =>
        `<option value="${esc(p.id)}" ${state.currentProject && p.id === state.currentProject.id ? "selected" : ""}>${esc(p.title)}</option>`
    )
    .join("");
}

async function selectProject(projectId) {
  if (!projectId) return;
  const data = await api(`/api/projects/${projectId}`);
  state.currentProject = data.project;
  state.chapters = data.chapters || [];
  renderProjectSelect();
  renderProjectMeta();
  renderChapterList();
  renderBible();

  if (state.chapters.length > 0) {
    const firstWritten = state.chapters.find((c) => c.content && c.content.trim()) || state.chapters[0];
    await selectChapter(firstWritten.chapter_number);
  } else {
    state.currentChapter = null;
    renderManuscript();
    renderAudit(null);
  }
  renderWorkspaceVisibility();
}

function renderProjectMeta() {
  const p = state.currentProject;
  if (!p) return;
  const bp = genreById(p.genre_id);
  const written = state.chapters.filter((c) => c.content && c.content.trim()).length;
  $("#project-meta").innerHTML = `
    <span class="genre-tag">${esc(bp.name)}</span>
    <div>已写 ${written} / ${p.target_chapters} 章</div>
    <div style="margin-top:4px">${esc(p.bible?.logline || p.premise)}</div>
  `;
}

function renderChapterList() {
  const ul = $("#chapter-list");
  if (!state.chapters.length) {
    ul.innerHTML = `<li class="muted-note">请先策划大纲</li>`;
    return;
  }
  ul.innerHTML = state.chapters
    .map((ch) => {
      const active = state.currentChapter && ch.chapter_number === state.currentChapter.chapter_number;
      let badgeText = "待执笔";
      let badgeCls = "";
      if (ch.audit && ch.content && ch.content.trim()) {
        const s = ch.audit.metrics.humanity_score;
        badgeText = `${s}分`;
        badgeCls = s >= 80 ? "good" : s >= 65 ? "warn" : "bad";
      } else if (ch.content && ch.content.trim()) {
        badgeText = "已写";
      }
      return `
        <li class="chapter-item ${active ? "active" : ""}" data-num="${ch.chapter_number}">
          <div class="chapter-item-main">
            <div class="chapter-item-num">第 ${ch.chapter_number} 章</div>
            <div class="chapter-item-title">${esc(ch.title)}</div>
          </div>
          <span class="ch-badge ${badgeCls}">${badgeText}</span>
        </li>`;
    })
    .join("");

  ul.querySelectorAll(".chapter-item").forEach((el) => {
    el.addEventListener("click", () => selectChapter(Number(el.dataset.num)));
  });
}

async function selectChapter(num) {
  if (!state.currentProject) return;
  const data = await api(`/api/projects/${state.currentProject.id}/chapters/${num}`);
  state.currentChapter = data.chapter;
  renderChapterList();
  renderManuscript();
  renderAudit(state.currentChapter.audit);
}

/* ---------- Rendering: Manuscript & Red-Pen Markup ---------- */
function buildMarkedHtml(text, slopIssues = []) {
  if (!text || !text.trim()) {
    return `<div class="manuscript-placeholder">本章尚无正文。点击右上角「执笔精工本章」，将自动完成场景分镜、反AI套话初稿、红笔质检、外科精修与连续性状态同步。</div>`;
  }
  const spans = (slopIssues || [])
    .filter((i) => typeof i.start === "number" && i.start >= 0 && i.end > i.start && i.end <= text.length)
    .sort((a, b) => a.start - b.start);

  let html = "";
  let cursor = 0;
  spans.forEach((issue, idx) => {
    if (issue.start < cursor) return;
    html += esc(text.slice(cursor, issue.start));
    const phrase = esc(text.slice(issue.start, issue.end));
    const tip = `${issue.explanation}｜建议：${issue.suggestion}`;
    html += `<span class="slop-mark sev-${esc(issue.severity)}" data-issue-idx="${idx}" title="${esc(tip)}">${phrase}</span>`;
    cursor = issue.end;
  });
  html += esc(text.slice(cursor));
  return html;
}

function renderManuscript() {
  const ch = state.currentChapter;
  if (!ch) return;

  $("#ch-num-badge").textContent = `第 ${ch.chapter_number} 章`;
  $("#ch-title-input").value = ch.title || "";
  $("#manuscript-editor").value = ch.content || "";

  // Scene beats drawer
  const beats = ch.beats || [];
  $("#beats-count").textContent = beats.length ? `共 ${beats.length} 个节拍` : "尚未拆解";
  $("#beats-list").innerHTML = beats.length
    ? beats
        .map(
          (b) => `
          <div class="beat-card">
            <strong>节拍 ${b.beat_index} · ${esc(b.location || "现场")}</strong>
            <p><b>目标：</b>${esc(b.goal)}</p>
            <p><b>阻力：</b>${esc(b.obstacle)}</p>
            <p><b>转折：</b>${esc(b.turn)}</p>
            <p><b>感官：</b>${esc(b.sensory_anchor)}</p>
          </div>`
        )
        .join("")
    : `<p class="muted-note">尚未生成场景分镜，可点击上方按钮先行拆解，或直接「执笔精工本章」自动生成。</p>`;

  // Markup surface
  const issues = ch.audit?.slop_issues || [];
  $("#manuscript-markup").innerHTML = buildMarkedHtml(ch.content || "", issues);

  // Diff view
  const rawText = ch.raw_content || ch.content || "";
  const revs = ch.revisions || [];
  const firstRev = revs[0];
  const lastRev = revs[revs.length - 1];
  $("#diff-before-score").textContent = firstRev ? `自然度 ${firstRev.humanity_score} 分` : "无初稿记录";
  $("#diff-after-score").textContent = ch.audit ? `自然度 ${ch.audit.metrics.humanity_score} 分` : (lastRev ? `${lastRev.humanity_score} 分` : "--");
  $("#diff-before-body").textContent = rawText || "尚无初稿";
  $("#diff-after-body").textContent = ch.content || "尚无精修稿";

  updateSheetModeVisibility();
}

function updateSheetModeVisibility() {
  $$(".seg-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.sheetMode === state.sheetMode)
  );
  $("#manuscript-markup").classList.toggle("hidden", state.sheetMode !== "markup");
  $("#manuscript-editor").classList.toggle("hidden", state.sheetMode !== "edit");
  $("#manuscript-diff").classList.toggle("hidden", state.sheetMode !== "diff");
}

/* ---------- Rendering: Story Bible ---------- */
function renderBible() {
  const p = state.currentProject;
  if (!p || !p.bible) {
    $("#bible-content").innerHTML = "";
    return;
  }
  const b = p.bible;
  const rulesHtml = (b.world_rules || [])
    .map(
      (r) => `
      <div class="rule-row">
        <strong>[${esc(r.category)}] ${esc(r.rule)}</strong>
        <div class="muted-note">代价与边界：${esc(r.cost_or_limit || "严格遵守")}</div>
      </div>`
    )
    .join("");

  const charsHtml = (b.characters || [])
    .map(
      (c) => `
      <div class="voice-card">
        <h4>${esc(c.name)}</h4>
        <div class="role-line">${esc(c.role)} · ${esc(c.age_or_identity)}</div>
        <p><b>核心诉求：</b>${esc(c.core_desire)}</p>
        <p><b>弱点/隐秘：</b>${esc(c.flaw_or_fear)} / ${esc(c.secret)}</p>
        <p><b>当前状态：</b>${esc(c.current_location)} · ${esc(c.current_state)}</p>
        <p><b>随身物品：</b>${esc((c.inventory || []).join("、") || "无")}</p>
        <p><b>说话声纹：</b>${esc(c.voice?.sentence_style || "")}；${esc(c.voice?.vocabulary_register || "")}</p>
        ${(c.voice?.sample_lines || [])
          .map((line) => `<div class="voice-quote">「${esc(line)}」</div>`)
          .join("")}
      </div>`
    )
    .join("");

  const cluesHtml = (b.foreshadowing || [])
    .map(
      (f) => `
      <div class="rule-row">
        <strong>${esc(f.title)}</strong>
        <span class="ch-badge ${f.status === "resolved" ? "good" : "warn"}">${esc(f.status)}</span>
        <div class="muted-note">第 ${f.planted_chapter} 章埋设 → 预计第 ${f.target_payoff_chapter || "?"} 章回收：${esc(f.description)}</div>
      </div>`
    )
    .join("");

  const outlinesHtml = (b.outlines || [])
    .map(
      (o) => `
      <div class="rule-row">
        <strong>第 ${o.chapter_number} 章 · ${esc(o.title)}</strong>（POV：${esc(o.pov || "主视角")}）
        <div>${esc(o.summary)}</div>
        <div class="muted-note">核心冲突：${esc(o.core_conflict)} ｜ 章末钩子：${esc(o.chapter_hook)}</div>
      </div>`
    )
    .join("");

  const timelineHtml = (b.timeline_log || []).length
    ? b.timeline_log.map((t) => `<div class="rule-row">${esc(t)}</div>`).join("")
    : `<p class="muted-note">随着各章定稿，系统会自动记录时间线推进与状态变化。</p>`;

  $("#bible-content").innerHTML = `
    <div class="bible-block">
      <h3>核心卖点与世界总览</h3>
      <p><b>一句话卖点：</b>${esc(b.logline || p.premise)}</p>
      <p><b>叙事基调与视角：</b>${esc(b.tone_and_style)} ｜ ${esc(b.narrative_pov)}</p>
      <p>${esc(b.world_overview)}</p>
    </div>
    <div class="bible-block">
      <h3>世界观铁律（防吃书红线）</h3>
      ${rulesHtml || `<p class="muted-note">暂无铁律</p>`}
    </div>
    <div class="bible-block">
      <h3>人物声纹卡（防千人一面）</h3>
      <div class="bible-grid">${charsHtml || `<p class="muted-note">暂无人物卡</p>`}</div>
    </div>
    <div class="bible-block">
      <h3>伏笔与线索账本</h3>
      ${cluesHtml || `<p class="muted-note">暂无伏笔记录</p>`}
    </div>
    <div class="bible-block">
      <h3>章节大纲</h3>
      ${outlinesHtml || `<p class="muted-note">暂无大纲</p>`}
    </div>
    <div class="bible-block">
      <h3>连续性时间线档案</h3>
      ${timelineHtml}
    </div>
  `;
}

/* ---------- Rendering: Right Audit Console ---------- */
function renderAudit(audit) {
  if (!audit || !audit.metrics) {
    $("#metric-humanity").textContent = "--";
    $("#metric-grade").textContent = "-";
    $("#metric-grade").classList.remove("bad");
    $("#metric-bar").style.width = "0%";
    $("#metric-risk").textContent = "--";
    $("#metric-burst").textContent = "--";
    $("#metric-dialogue").textContent = "--";
    $("#metric-chars").textContent = "--";
    $("#audit-verdict").textContent = "尚未生成或体检本章正文。";
    $("#slop-count").textContent = "0";
    $("#continuity-count").textContent = "0";
    $("#slop-issue-list").innerHTML = `<p class="muted-note">暂无批注。</p>`;
    $("#continuity-issue-list").innerHTML = `<p class="muted-note">暂无逻辑问题。</p>`;
    return;
  }

  const m = audit.metrics;
  $("#metric-humanity").textContent = `${m.humanity_score}`;
  $("#metric-grade").textContent = m.grade;
  $("#metric-grade").classList.toggle("bad", m.humanity_score < 65);
  $("#metric-bar").style.width = `${Math.max(4, Math.min(100, m.humanity_score))}%`;
  $("#metric-risk").textContent = `${m.ai_risk_score}`;
  $("#metric-burst").textContent = `${m.burstiness_score}`;
  $("#metric-dialogue").textContent = `${Math.round(m.dialogue_ratio * 100)}%`;
  $("#metric-chars").textContent = `${m.char_count}`;
  $("#audit-verdict").textContent = audit.summary || "";

  const slops = audit.slop_issues || [];
  $("#slop-count").textContent = String(slops.length);
  if (!slops.length) {
    $("#slop-issue-list").innerHTML = `<p class="muted-note">未检出明显 AI 套话、直白情绪播报或说教结尾。</p>`;
  } else {
    let spanIdx = 0;
    $("#slop-issue-list").innerHTML = slops
      .map((item) => {
        const hasSpan = typeof item.start === "number" && item.start >= 0;
        const targetAttr = hasSpan ? `data-target-span="${spanIdx++}"` : "";
        return `
          <div class="issue-card sev-${esc(item.severity)}" ${targetAttr}>
            <div class="issue-phrase">L${item.line} · ${esc(item.phrase)}</div>
            <div class="issue-exp">${esc(item.explanation)}</div>
            <div class="issue-fix">建议：${esc(item.suggestion)}</div>
          </div>`;
      })
      .join("");

    $$("#slop-issue-list .issue-card[data-target-span]").forEach((card) => {
      card.addEventListener("click", () => {
        if (state.activeView !== "manuscript") switchView("manuscript");
        if (state.sheetMode !== "markup") {
          state.sheetMode = "markup";
          updateSheetModeVisibility();
        }
        const idx = card.dataset.targetSpan;
        const mark = $(`#manuscript-markup .slop-mark[data-issue-idx="${idx}"]`);
        if (mark) {
          mark.scrollIntoView({ behavior: "smooth", block: "center" });
          mark.classList.add("pulse");
          setTimeout(() => mark.classList.remove("pulse"), 1400);
        }
      });
    });
  }

  const conts = audit.continuity_issues || [];
  $("#continuity-count").textContent = String(conts.length);
  if (!conts.length) {
    $("#continuity-issue-list").innerHTML = `<p class="muted-note">未发现设定冲突、人物 OOC 或时间线漏洞。</p>`;
  } else {
    $("#continuity-issue-list").innerHTML = conts
      .map(
        (c) => `
        <div class="issue-card sev-${esc(c.severity)}">
          <div class="issue-phrase">${esc(c.category)} · ${esc(c.excerpt || "整章")}</div>
          <div class="issue-exp">${esc(c.explanation)}</div>
          <div class="issue-fix">改法：${esc(c.fix_hint)}</div>
        </div>`
      )
      .join("");
  }
}

/* ---------- View & Modal Management ---------- */
function renderWorkspaceVisibility() {
  const hasProject = Boolean(state.currentProject);
  const showEmpty = !hasProject && state.activeView !== "tool";
  $("#empty-state").classList.toggle("hidden", !showEmpty);
  $("#view-manuscript").classList.toggle("hidden", showEmpty || state.activeView !== "manuscript");
  $("#view-bible").classList.toggle("hidden", showEmpty || state.activeView !== "bible");
  $("#view-tool").classList.toggle("hidden", state.activeView !== "tool");
}

function switchView(view) {
  state.activeView = view;
  $$(".tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  renderWorkspaceVisibility();
}

function openModal(id) {
  $(`#${id}`).classList.remove("hidden");
}

function closeModal(id) {
  $(`#${id}`).classList.add("hidden");
}

/* ---------- Event Wiring ---------- */
function bindEvents() {
  // Top tabs
  $$(".tab-btn").forEach((btn) =>
    btn.addEventListener("click", () => switchView(btn.dataset.view))
  );

  // Sheet sub-mode switcher
  $$(".seg-btn").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.sheetMode = btn.dataset.sheetMode;
      updateSheetModeVisibility();
    })
  );

  // Close modals
  $$("[data-close]").forEach((btn) =>
    btn.addEventListener("click", () => closeModal(btn.dataset.close))
  );

  // Project select
  $("#project-select").addEventListener("change", (e) => {
    if (e.target.value) selectProject(e.target.value);
  });

  // Delete project
  $("#btn-delete-project").addEventListener("click", async () => {
    if (!state.currentProject) return;
    if (!confirm(`确认删除小说《${state.currentProject.title}》及全部章节？`)) return;
    await api(`/api/projects/${state.currentProject.id}`, { method: "DELETE" });
    showToast("已删除书目");
    const pRes = await api("/api/projects");
    state.projects = pRes.projects || [];
    state.currentProject = null;
    state.chapters = [];
    state.currentChapter = null;
    renderProjectSelect();
    if (state.projects.length) {
      await selectProject(state.projects[0].id);
    } else {
      renderAudit(null);
      renderWorkspaceVisibility();
    }
  });

  // New project modal
  const openNew = () => openModal("modal-new");
  $("#btn-new-project").addEventListener("click", openNew);
  $("#btn-empty-new").addEventListener("click", openNew);

  $("#btn-fill-sample-premise").addEventListener("click", () => {
    const bp = genreById(state.selectedNewGenre);
    $("#new-premise").value = bp.sample_premise || "";
    if (!$("#new-title").value.trim()) {
      $("#new-title").value = `${bp.name.split(" / ")[0]}·新篇`;
    }
  });

  $$("#style-presets .style-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      $("#new-style").value = pill.dataset.style || "";
    });
  });

  $("#form-new-project").addEventListener("submit", async (e) => {
    e.preventDefault();
    closeModal("modal-new");
    setBusy(true, "正在构建世界观铁律、人物声纹卡与全书章节大纲…");
    try {
      const data = await api("/api/projects", {
        method: "POST",
        body: JSON.stringify({
          title: $("#new-title").value.trim(),
          genre_id: state.selectedNewGenre,
          premise: $("#new-premise").value.trim(),
          style_notes: $("#new-style").value.trim(),
          target_chapters: Number($("#new-chapters").value) || 6,
          target_words_per_chapter: Number($("#new-words").value) || 2600,
          auto_plan: true,
        }),
      });
      const pRes = await api("/api/projects");
      state.projects = pRes.projects || [];
      await selectProject(data.project.id);
      switchView("manuscript");
      showToast("项目已创建，故事圣经与大纲已生成");
      $("#form-new-project").reset();
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  // Quick 1-click suspense demo
  $("#btn-quick-demo").addEventListener("click", async () => {
    const bp = genreById("suspense");
    setBusy(true, "正在创建悬疑示例并执行全链路「分镜 → 初稿 → 去AI体检 → 精修」…");
    try {
      const created = await api("/api/projects", {
        method: "POST",
        body: JSON.stringify({
          title: "雨夜十五分钟",
          genre_id: "suspense",
          premise: bp.sample_premise,
          target_chapters: 6,
          auto_plan: true,
        }),
      });
      await api(`/api/projects/${created.project.id}/chapters/1/generate`, {
        method: "POST",
        body: JSON.stringify({ mode: "craft" }),
      });
      const pRes = await api("/api/projects");
      state.projects = pRes.projects || [];
      await selectProject(created.project.id);
      state.sheetMode = "diff";
      switchView("manuscript");
      updateSheetModeVisibility();
      showToast("示例小说第 1 章已生成，正在展示初稿与去AI精修前后对比");
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  // Chapter actions
  $("#btn-gen-beats").addEventListener("click", async () => {
    if (!state.currentProject || !state.currentChapter) return;
    setBusy(true, "正在拆解本章场景分镜…");
    try {
      const data = await api(
        `/api/projects/${state.currentProject.id}/chapters/${state.currentChapter.chapter_number}/beats`,
        { method: "POST" }
      );
      state.currentChapter = data.chapter;
      renderManuscript();
      $("#beats-drawer").open = true;
      showToast("场景分镜已更新");
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  $("#btn-gen-chapter").addEventListener("click", async () => {
    if (!state.currentProject || !state.currentChapter) return;
    const num = state.currentChapter.chapter_number;
    setBusy(true, `正在精工执笔第 ${num} 章（分镜 → 初稿 → 去AI体检 → 外科精修 → 同步设定）…`);
    try {
      const data = await api(
        `/api/projects/${state.currentProject.id}/chapters/${num}/generate`,
        { method: "POST", body: JSON.stringify({ mode: "craft" }) }
      );
      state.currentChapter = data.chapter;
      if (data.project) state.currentProject = data.project;
      const pDetail = await api(`/api/projects/${state.currentProject.id}`);
      state.chapters = pDetail.chapters || [];
      renderProjectMeta();
      renderChapterList();
      renderBible();
      renderManuscript();
      renderAudit(state.currentChapter.audit);
      showToast(`第 ${num} 章精工定稿完成`);
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  $("#btn-polish-chapter").addEventListener("click", async () => {
    if (!state.currentProject || !state.currentChapter) return;
    const num = state.currentChapter.chapter_number;
    setBusy(true, `正在对第 ${num} 章执行去AI味外科手术精修…`);
    try {
      const data = await api(
        `/api/projects/${state.currentProject.id}/chapters/${num}/polish`,
        { method: "POST" }
      );
      state.currentChapter = data.chapter;
      const pDetail = await api(`/api/projects/${state.currentProject.id}`);
      state.chapters = pDetail.chapters || [];
      renderChapterList();
      renderManuscript();
      renderAudit(state.currentChapter.audit);
      showToast("去AI味精修完成，可切换「精修对比」查看差异");
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  $("#btn-save-chapter").addEventListener("click", async () => {
    if (!state.currentProject || !state.currentChapter) return;
    const num = state.currentChapter.chapter_number;
    const content =
      state.sheetMode === "edit"
        ? $("#manuscript-editor").value
        : state.currentChapter.content;
    const title = $("#ch-title-input").value.trim();
    try {
      const data = await api(
        `/api/projects/${state.currentProject.id}/chapters/${num}`,
        { method: "PUT", body: JSON.stringify({ title, content }) }
      );
      state.currentChapter = data.chapter;
      const pDetail = await api(`/api/projects/${state.currentProject.id}`);
      state.chapters = pDetail.chapters || [];
      renderChapterList();
      renderManuscript();
      renderAudit(state.currentChapter.audit);
      showToast("已保存并刷新红笔体检");
    } catch (err) {
      showToast(err.message, true);
    }
  });

  $("#btn-reaudit").addEventListener("click", async () => {
    if (!state.currentProject || !state.currentChapter) return;
    try {
      const data = await api(
        `/api/projects/${state.currentProject.id}/chapters/${state.currentChapter.chapter_number}/audit`,
        { method: "POST" }
      );
      state.currentChapter.audit = data.audit;
      renderManuscript();
      renderAudit(data.audit);
      showToast("红笔体检已刷新");
    } catch (err) {
      showToast(err.message, true);
    }
  });

  $("#btn-replan").addEventListener("click", async () => {
    if (!state.currentProject) return;
    setBusy(true, "正在重新策划故事圣经与章节大纲…");
    try {
      const data = await api(`/api/projects/${state.currentProject.id}/plan`, { method: "POST" });
      state.currentProject = data.project;
      state.chapters = data.chapters || [];
      renderProjectMeta();
      renderChapterList();
      renderBible();
      showToast("故事圣经已更新");
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  // Batch modal
  $("#btn-batch-open").addEventListener("click", () => {
    if (!state.currentProject) return showToast("请先新建或选择一个项目", true);
    $("#batch-start").value = 1;
    $("#batch-end").value = Math.min(3, state.currentProject.target_chapters);
    openModal("modal-batch");
  });

  $("#form-batch").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.currentProject) return;
    const s = Number($("#batch-start").value);
    const end = Number($("#batch-end").value);
    const mode = $("#batch-mode").value;
    closeModal("modal-batch");
    setBusy(true, `正在连续生成第 ${s} 至第 ${end} 章，请稍候…`);
    try {
      await api(`/api/projects/${state.currentProject.id}/batch`, {
        method: "POST",
        body: JSON.stringify({ start_chapter: s, end_chapter: end, mode }),
      });
      await selectProject(state.currentProject.id);
      await selectChapter(s);
      showToast(`第 ${s}-${end} 章连续生成完成`);
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });

  // Export dropdown
  $("#btn-export-toggle").addEventListener("click", (e) => {
    e.stopPropagation();
    $("#export-dropdown").classList.toggle("open");
  });
  document.addEventListener("click", () => $("#export-dropdown").classList.remove("open"));
  $$("#export-menu button").forEach((btn) =>
    btn.addEventListener("click", () => {
      if (!state.currentProject) return showToast("请先选择一部小说", true);
      const fmt = btn.dataset.fmt;
      window.location.href = `/api/projects/${state.currentProject.id}/export/${fmt}`;
    })
  );

  // Settings modal
  const syncPresetHint = (providerId) => {
    const p = state.presets.find((x) => x.id === providerId);
    $("#set-provider-hint").textContent = p ? p.hint : "";
    if (p) {
      $("#set-baseurl").placeholder = p.base_url || "（离线演示模式无需地址）";
      $("#set-model").placeholder = p.default_model;
      $("#set-fast-model").placeholder = p.fast_model;
    }
  };

  $("#set-provider").addEventListener("change", (e) => syncPresetHint(e.target.value));
  $("#btn-settings").addEventListener("click", () => {
    const cur = state.settings || { provider: "demo" };
    $("#set-provider").value = cur.provider;
    $("#set-apikey").value = "";
    $("#set-apikey").placeholder = cur.has_api_key ? `已保存（${cur.api_key_masked}），留空保持不变` : "sk-...";
    $("#set-baseurl").value = cur.base_url || "";
    $("#set-model").value = cur.model || "";
    $("#set-fast-model").value = cur.fast_model || "";
    syncPresetHint(cur.provider);
    openModal("modal-settings");
  });

  $("#form-settings").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const keyVal = $("#set-apikey").value.trim();
      const body = {
        provider: $("#set-provider").value,
        base_url: $("#set-baseurl").value.trim(),
        model: $("#set-model").value.trim(),
        fast_model: $("#set-fast-model").value.trim(),
      };
      if (keyVal) body.api_key = keyVal;
      const res = await api("/api/settings", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      state.settings = res.current;
      renderSettingsBadge();
      closeModal("modal-settings");
      showToast("模型配置已保存");
    } catch (err) {
      showToast(err.message, true);
    }
  });

  // Standalone Anti-AI-Slop Tool
  $("#btn-tool-sample").addEventListener("click", () => {
    $("#tool-input").value =
      "夜幕降临，城市的霓虹灯闪烁，宛如一幅流动的画卷。林川站在落地窗前，深吸了一口气，感到一阵难以言喻的压迫感。\n\n" +
      "空气仿佛凝固了。对方缓缓说道，眼神深邃地盯着他：“值得注意的是，这份合同的漏洞远比你想象的要大。”\n\n" +
      "林川嘴角勾起一抹冷笑，眼中闪过一丝寒意，不禁握紧了拳头。然而，与此同时，会议室的门被推开了，气氛瞬间变得凝重起来。\n\n" +
      "这一刻，他终于明白，命运的齿轮已经悄然转动，前方的路还很长，真正的较量才刚刚开始。";
  });

  $("#btn-tool-audit").addEventListener("click", async () => {
    const text = $("#tool-input").value.trim();
    if (!text) return showToast("请先粘贴待体检文本", true);
    try {
      const res = await api("/api/tools/audit", {
        method: "POST",
        body: JSON.stringify({ text, genre_id: $("#tool-genre-select").value }),
      });
      const a = res.audit;
      const badge = $("#tool-score-badge");
      badge.textContent = `自然度 ${a.metrics.humanity_score} 分（${a.metrics.grade}级 · AI味风险 ${a.metrics.ai_risk_score}）`;
      badge.classList.remove("hidden");
      $("#tool-output").innerHTML = buildMarkedHtml(text, a.slop_issues);
      renderAudit(a);
    } catch (err) {
      showToast(err.message, true);
    }
  });

  $("#btn-tool-polish").addEventListener("click", async () => {
    const text = $("#tool-input").value.trim();
    if (!text) return showToast("请先粘贴待精修文本", true);
    setBusy(true, "正在执行去AI味外科手术精修…");
    try {
      const res = await api("/api/tools/polish", {
        method: "POST",
        body: JSON.stringify({ text, genre_id: $("#tool-genre-select").value }),
      });
      const b = res.before_audit.metrics.humanity_score;
      const a = res.after_audit.metrics.humanity_score;
      const delta = res.score_delta;
      const badge = $("#tool-score-badge");
      badge.textContent = `自然度 ${b} → ${a}（${delta >= 0 ? "+" : ""}${delta} 分）`;
      badge.classList.remove("hidden");
      $("#tool-output").innerHTML = buildMarkedHtml(
        res.polished_text,
        res.after_audit.slop_issues
      );
      renderAudit(res.after_audit);
      showToast("去AI味精修完成");
    } catch (err) {
      showToast(err.message, true);
    } finally {
      setBusy(false);
    }
  });
}

init();
