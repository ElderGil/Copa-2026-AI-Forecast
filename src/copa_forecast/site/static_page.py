from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def render_static_page(*, latest: dict[str, Any], github_url: str, output_dir: str | Path) -> None:
    target = Path(output_dir)
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "latest.json").write_text(
        json.dumps(latest, indent=2, sort_keys=True), encoding="utf-8"
    )
    teams = sorted(latest.get("teams", []), key=lambda row: row["rank"])
    top = teams[:10]
    podium = "".join(_team_card(team, large=team["rank"] <= 3) for team in top[:3])
    rest = "".join(_ranking_row(team) for team in top[3:])
    grid = "".join(_team_card(team, large=False) for team in teams)
    data = json.dumps(latest, ensure_ascii=False).replace("</", "<\\/")
    markup = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Copa 2026 AI Forecast</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <strong>Copa 2026 AI Forecast</strong>
    <a href="{html.escape(github_url)}">GitHub</a>
  </header>
  <main>
    <section class="hero">
      <div class="hero-copy">
        <p>{html.escape(str(latest.get("updated_at", "")))}</p>
        <h1>Top 10 probabilidades de titulo</h1>
        <div class="run-meta">
          <span>{html.escape(str(latest.get("model_version", "")))}</span>
          <span>{html.escape(str(latest.get("calibration_status", "")))}</span>
        </div>
      </div>
      <div class="top-board">
        <div class="podium">{podium}</div>
        <ol class="top-list">{rest}</ol>
      </div>
    </section>
    <section class="all-teams">
      <div class="section-heading">
        <h2>Todas as selecoes</h2>
        <p>{len(teams)} selecoes no snapshot atual</p>
      </div>
      <div class="team-grid" aria-label="Todas as selecoes">{grid}</div>
    </section>
  </main>
  <div class="panel-scrim" data-close-panel></div>
  <aside class="team-panel" id="team-panel" aria-hidden="true" aria-label="Detalhes da selecao">
    <button class="panel-close" type="button" data-close-panel aria-label="Fechar">X</button>
    <div class="panel-head">
      <span class="panel-rank" data-panel-rank></span>
      <span class="flag-badge" data-panel-flag></span>
      <h2 data-panel-team></h2>
      <strong data-panel-probability></strong>
    </div>
    <dl class="panel-stats">
      <div><dt>Grupo</dt><dd data-panel-group></dd></div>
      <div><dt>Pontos</dt><dd data-panel-points></dd></div>
      <div><dt>Saldo</dt><dd data-panel-goal-difference></dd></div>
      <div><dt>Forca</dt><dd data-panel-strength></dd></div>
    </dl>
    <p class="panel-summary" data-panel-summary></p>
    <h3>Pilares usados</h3>
    <div class="pillar-list" data-panel-used></div>
    <h3>Pilares excluidos</h3>
    <div class="pillar-list" data-panel-excluded></div>
    <h3>Benchmarks</h3>
    <div class="pillar-list" data-panel-benchmarks></div>
  </aside>
  <script id="forecast-data" type="application/json">{data}</script>
  <script src="app.js"></script>
</body>
</html>
"""
    (target / "index.html").write_text(markup, encoding="utf-8")
    (target / "styles.css").write_text(_styles(), encoding="utf-8")
    (target / "app.js").write_text(_script(), encoding="utf-8")


def _team_card(team: dict[str, Any], *, large: bool) -> str:
    klass = "team-card large" if large else "team-card"
    return (
        f'<button class="{klass}" type="button" data-team="{html.escape(team["team"])}">'
        f'<span class="rank">#{team["rank"]}</span>'
        f'<span class="flag-badge">{html.escape(team.get("flag", ""))}</span>'
        f'<span class="name">{html.escape(team["team"])}</span>'
        f'<strong>{team["champion_probability"]:.1%}</strong>'
        "</button>"
    )


def _ranking_row(team: dict[str, Any]) -> str:
    return (
        f'<li><button type="button" data-team="{html.escape(team["team"])}">'
        f'<span>#{team["rank"]} {html.escape(team["team"])}</span>'
        f'<strong>{team["champion_probability"]:.1%}</strong></button></li>'
    )


def _styles() -> str:
    return """
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #f4f1ea; color: #17211b; }
button, a { font: inherit; }
.site-header { min-height: 64px; display:flex; align-items:center; justify-content:space-between; padding:16px 28px; background:#fffaf0; border-bottom:1px solid #ded8ca; position:sticky; top:0; z-index:10; }
a { color:#b91c1c; font-weight:800; text-decoration:none; }
.hero { min-height: calc(100vh - 64px); padding: 34px 28px 28px; display:grid; grid-template-columns: minmax(280px, 0.72fr) minmax(420px, 1.28fr); gap:28px; align-items:center; background:#113a2b; color:#fffaf0; }
.hero-copy { display:grid; gap:22px; align-content:center; }
.hero-copy p { margin:0; color:#d7e3da; font-weight:700; }
h1 { font-size: 58px; line-height:1; margin:0; max-width: 680px; }
.run-meta { display:flex; flex-wrap:wrap; gap:10px; }
.run-meta span { border:1px solid #8bb79f; border-radius:999px; padding:8px 12px; color:#f4f1ea; background:rgba(255,255,255,.08); }
.top-board { display:grid; gap:14px; }
.podium { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:14px; align-items:stretch; }
.team-card { min-height:142px; border:1px solid #d8d0bf; background:#fffdf8; color:#17211b; border-radius:8px; padding:18px; display:grid; gap:8px; text-align:left; cursor:pointer; box-shadow:0 8px 18px rgba(23,33,27,.08); }
.team-card:hover, .team-card:focus-visible, .top-list button:hover, .top-list button:focus-visible { outline:3px solid #f4c430; outline-offset:2px; }
.team-card.large { min-height:230px; align-content:end; border-color:#f4c430; color:#fffaf0; background:linear-gradient(155deg,#1e5f45,#8b1e22); }
.team-card .name { font-weight:800; font-size:20px; overflow-wrap:anywhere; }
.team-card strong { font-size:28px; }
.team-card.large strong { font-size:34px; }
.flag-badge { min-width:44px; min-height:34px; width:max-content; display:inline-grid; place-items:center; border-radius:4px; padding:5px 8px; background:#f4c430; color:#17211b; font-weight:900; }
.rank { color:#6e786f; font-weight:800; }
.team-card.large .rank { color:#f7e9b5; }
.top-list { list-style:none; padding:0; margin:0; display:grid; gap:10px; }
.top-list li { margin:0; }
.top-list button { width:100%; min-height:52px; display:flex; align-items:center; justify-content:space-between; gap:12px; border:1px solid #d8d0bf; background:#fffdf8; color:#17211b; padding:14px; border-radius:8px; cursor:pointer; }
.top-list strong { color:#8b1e22; }
.all-teams { padding: 30px 28px 46px; }
.section-heading { display:flex; align-items:end; justify-content:space-between; gap:18px; margin-bottom:18px; }
.section-heading h2 { font-size:32px; margin:0; }
.section-heading p { margin:0; color:#59645c; font-weight:700; }
.team-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap:14px; }
.panel-scrim { position:fixed; inset:0; background:rgba(17,30,24,.42); opacity:0; pointer-events:none; transition:opacity .18s ease; z-index:20; }
.team-panel { position:fixed; top:0; right:0; width:min(430px, 100vw); height:100vh; overflow:auto; transform:translateX(100%); transition:transform .2s ease; background:#fffdf8; color:#17211b; z-index:30; box-shadow:-24px 0 40px rgba(17,30,24,.22); padding:28px; }
body.panel-open .panel-scrim { opacity:1; pointer-events:auto; }
body.panel-open .team-panel { transform:translateX(0); }
.panel-close { position:absolute; top:16px; right:16px; width:42px; height:42px; border:1px solid #d8d0bf; border-radius:8px; background:#fffaf0; cursor:pointer; font-weight:900; }
.panel-head { display:grid; gap:10px; padding-right:42px; }
.panel-head h2 { font-size:34px; line-height:1; margin:0; overflow-wrap:anywhere; }
.panel-head strong { font-size:32px; color:#8b1e22; }
.panel-rank { color:#59645c; font-weight:900; }
.panel-stats { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:10px; margin:24px 0; }
.panel-stats div { border:1px solid #d8d0bf; border-radius:8px; padding:12px; background:#fffaf0; }
.panel-stats dt { color:#59645c; font-size:13px; font-weight:800; }
.panel-stats dd { margin:4px 0 0; font-size:22px; font-weight:900; }
.panel-summary { line-height:1.45; color:#36433a; }
.team-panel h3 { margin:24px 0 10px; font-size:18px; }
.pillar-list { display:grid; gap:8px; }
.pillar-item { border:1px solid #d8d0bf; border-left:5px solid #1e5f45; border-radius:8px; padding:11px 12px; background:#fffaf0; }
.pillar-item.excluded { border-left-color:#8b1e22; }
.pillar-item strong { display:block; }
.pillar-item span { display:block; margin-top:3px; color:#59645c; font-size:13px; }
@media (max-width: 980px) {
  .hero { grid-template-columns: 1fr; align-items:start; }
  h1 { font-size: 44px; }
}
@media (max-width: 680px) {
  .site-header { padding:14px 18px; }
  .hero { padding:24px 18px; }
  h1 { font-size: 36px; }
  .podium { grid-template-columns: 1fr; }
  .all-teams { padding:24px 18px 36px; }
  .section-heading { align-items:start; flex-direction:column; }
  .panel-stats { grid-template-columns:1fr; }
}
"""


def _script() -> str:
    return """
const latest = JSON.parse(document.getElementById('forecast-data').textContent);
const teams = new Map((latest.teams || []).map((team) => [team.team, team]));
const pillars = new Map((latest.pillars || []).map((pillar) => [pillar.key, pillar]));
const panel = document.getElementById('team-panel');

function percent(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value || 0);
}

function number(value) {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 }).format(value || 0);
}

function setText(selector, value) {
  const element = panel.querySelector(selector);
  if (element) element.textContent = value == null || value === '' ? '-' : value;
}

function pillarItem(key, variant) {
  const pillar = pillars.get(key) || { label: key, coverage: 0, source: '' };
  const item = document.createElement('div');
  item.className = `pillar-item ${variant}`;
  const title = document.createElement('strong');
  title.textContent = pillar.label || key;
  const meta = document.createElement('span');
  meta.textContent = `${percent(pillar.coverage)} cobertura | ${pillar.source || 'fonte pendente'}`;
  item.append(title, meta);
  return item;
}

function renderPillars(selector, keys, variant) {
  const target = panel.querySelector(selector);
  target.replaceChildren();
  if (!keys || keys.length === 0) {
    const empty = document.createElement('div');
    empty.className = `pillar-item ${variant}`;
    empty.textContent = '-';
    target.append(empty);
    return;
  }
  keys.forEach((key) => target.append(pillarItem(key, variant)));
}

function renderBenchmarks() {
  const target = panel.querySelector('[data-panel-benchmarks]');
  target.replaceChildren();
  (latest.benchmarks || []).forEach((benchmark) => {
    const item = document.createElement('div');
    item.className = 'pillar-item excluded';
    const title = document.createElement('strong');
    title.textContent = benchmark.label || benchmark.key;
    const meta = document.createElement('span');
    meta.textContent = `${benchmark.status || ''} | ${benchmark.source || ''}`;
    item.append(title, meta);
    target.append(item);
  });
}

function openPanel(teamName) {
  const team = teams.get(teamName);
  if (!team) return;
  const signal = team.tournament_signal || {};
  setText('[data-panel-rank]', `#${team.rank}`);
  setText('[data-panel-flag]', team.flag);
  setText('[data-panel-team]', team.team);
  setText('[data-panel-probability]', percent(team.champion_probability));
  setText('[data-panel-group]', team.group);
  setText('[data-panel-points]', signal.points);
  setText('[data-panel-goal-difference]', signal.goal_difference);
  setText('[data-panel-strength]', number(team.strength));
  setText('[data-panel-summary]', team.summary);
  renderPillars('[data-panel-used]', team.used_pillars || [], 'used');
  renderPillars('[data-panel-excluded]', team.excluded_pillars || [], 'excluded');
  renderBenchmarks();
  document.body.classList.add('panel-open');
  panel.setAttribute('aria-hidden', 'false');
}

function closePanel() {
  document.body.classList.remove('panel-open');
  panel.setAttribute('aria-hidden', 'true');
}

document.addEventListener('click', (event) => {
  const card = event.target.closest('[data-team]');
  if (card) openPanel(card.dataset.team);
  if (event.target.closest('[data-close-panel]')) closePanel();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closePanel();
});
"""
