from __future__ import annotations

import html
import json
from pathlib import Path
from shutil import copyfile
from typing import Any

from copa_forecast.reporting.countries import display_team_name, flag_emoji

# ---------------------------------------------------------------------------
# Dados editoriais fixos — fontes externas (atualizar manualmente quando mudar)
# ---------------------------------------------------------------------------
_MEDIA_FAVORITES: list[dict[str, Any]] = [
    {
        "source": "GE / Globo Esporte",
        "source_url": "https://ge.globo.com/futebol/copa-do-mundo/2026/noticia/2026/06/17/copa-2026-veja-os-favoritos-segundo-as-casas-de-apostas.ghtml",
        "collected_at": "2026-06-18",
        "teams": [
            {"rank": 1, "flag": "🇦🇷", "name": "Argentina"},
            {"rank": 2, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "name": "Inglaterra"},
            {"rank": 3, "flag": "🇫🇷", "name": "França"},
            {"rank": 4, "flag": "🇩🇪", "name": "Alemanha"},
            {"rank": 5, "flag": "🇪🇸", "name": "Espanha"},
            {"rank": 6, "flag": "🇧🇷", "name": "Brasil"},
            {"rank": 7, "flag": "🇵🇹", "name": "Portugal"},
            {"rank": 8, "flag": "🇳🇱", "name": "Países Baixos"},
            {"rank": 9, "flag": "🇧🇪", "name": "Bélgica"},
            {"rank": 10, "flag": "🇺🇸", "name": "EUA"},
        ],
    },
    {
        "source": "SporTV / Casas de Apostas",
        "source_url": "https://sportv.globo.com/site/programas/sportv-news/noticia/2026/06/copa-2026-veja-favoritos-apontados-pelas-principais-casas-de-apostas.ghtml",
        "collected_at": "2026-06-18",
        "teams": [
            {"rank": 1, "flag": "🇦🇷", "name": "Argentina"},
            {"rank": 2, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "name": "Inglaterra"},
            {"rank": 3, "flag": "🇫🇷", "name": "França"},
            {"rank": 4, "flag": "🇩🇪", "name": "Alemanha"},
            {"rank": 5, "flag": "🇪🇸", "name": "Espanha"},
            {"rank": 6, "flag": "🇧🇷", "name": "Brasil"},
            {"rank": 7, "flag": "🇵🇹", "name": "Portugal"},
            {"rank": 8, "flag": "🇳🇱", "name": "Países Baixos"},
            {"rank": 9, "flag": "🇳🇴", "name": "Noruega"},
            {"rank": 10, "flag": "🇧🇪", "name": "Bélgica"},
        ],
    },
    {
        "source": "FIFA Power Rankings by Aramco",
        "source_url": "https://www.fifa.com/pt/tournaments/mens/worldcup/canadamexicousa2026/power-rankings",
        "collected_at": "2026-06-18",
        "note": "Ranking de força publicado pela FIFA antes da Copa — baseado em desempenho histórico e forma recente.",
        "teams": [
            {"rank": 1, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "name": "Inglaterra"},
            {"rank": 2, "flag": "🇩🇪", "name": "Alemanha"},
            {"rank": 3, "flag": "🇦🇷", "name": "Argentina"},
            {"rank": 4, "flag": "🇫🇷", "name": "França"},
            {"rank": 5, "flag": "🇪🇸", "name": "Espanha"},
            {"rank": 6, "flag": "🇵🇹", "name": "Portugal"},
            {"rank": 7, "flag": "🇧🇷", "name": "Brasil"},
            {"rank": 8, "flag": "🇳🇱", "name": "Países Baixos"},
            {"rank": 9, "flag": "🇲🇦", "name": "Marrocos"},
            {"rank": 10, "flag": "🇺🇸", "name": "EUA"},
        ],
    },
]


def render_static_page(*, latest: dict[str, Any], github_url: str, output_dir: str | Path) -> None:
    target = Path(output_dir)
    data_dir = target / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _copy_site_assets(target)
    latest = _enrich_display_payload(latest)
    (data_dir / "latest.json").write_text(
        json.dumps(latest, indent=2, sort_keys=True), encoding="utf-8"
    )
    teams = sorted(latest.get("teams", []), key=lambda row: row["rank"])
    top = teams[:10]
    podium = "".join(_team_card(team, large=team["rank"] <= 3) for team in top[:3])
    rest = "".join(_ranking_row(team) for team in top[3:])
    grid = "".join(_team_card(team, large=False) for team in teams)
    data = json.dumps(latest, ensure_ascii=False).replace("</", "<\\/")

    # Metadados formatados para o header
    updated_raw = str(latest.get("updated_at", ""))
    updated_friendly = _format_date_friendly(updated_raw)
    model_version = str(latest.get("model_version", ""))
    as_of_date = str(latest.get("as_of_date", ""))

    # Seção de favoritos das mídias
    media_section = _render_media_favorites()

    markup = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Copa 2026 AI Forecast — Previsão com Inteligência Artificial</title>
  <meta name="description" content="Previsão estatística das probabilidades de título na Copa do Mundo 2026, gerada por modelo de IA com dados oficiais da FIFA. Atualizado diariamente.">
  <meta property="og:title" content="Copa 2026 AI Forecast">
  <meta property="og:description" content="Probabilidades de título geradas por IA com dados oficiais da FIFA. Modelo {html.escape(model_version)}.">
  <meta property="og:url" content="https://eldergil.github.io/Copa-2026-AI-Forecast/">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <strong class="site-title">⚽ Copa 2026 AI Forecast</strong>
    <a href="{html.escape(github_url)}" class="gh-link" target="_blank" rel="noopener noreferrer" aria-label="Ver código no GitHub">
      <svg class="gh-icon" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/></svg>
      GitHub
    </a>
  </header>
  <main>
    <section class="hero">
      <div class="hero-copy">
        <div class="run-stamp">
          <span class="run-stamp-label">Atualizado em</span>
          <span class="run-stamp-value">{html.escape(updated_friendly)}</span>
          <span class="run-stamp-sub">Dados de {html.escape(as_of_date)}</span>
        </div>
        <h1>Top 10 probabilidades de título</h1>
        <div class="run-meta">
          <span class="run-meta-version" title="Versão do modelo preditivo">
            <span class="run-meta-icon">🤖</span>
            Modelo: <strong>{html.escape(model_version)}</strong>
          </span>
          <span class="run-meta-calib" title="O modelo ainda não passou por calibração probabilística formal. As probabilidades são baseadas em forma recente, nível dos adversários e ranking FIFA/SUM.">
            <span class="run-meta-icon">⚠️</span>
            Baseline · não calibrado
          </span>
        </div>
      </div>
      <div class="top-board">
        <div class="podium">{podium}</div>
        <ol class="top-list">{rest}</ol>
      </div>
    </section>
    {media_section}
    <section class="all-teams">
      <div class="section-heading">
        <h2>Todas as seleções</h2>
        <p>{len(teams)} seleções no snapshot atual</p>
      </div>
      <div class="team-grid" aria-label="Todas as seleções">{grid}</div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <strong>⚽ Copa 2026 AI Forecast</strong>
        <span>Previsão estatística com dados oficiais da FIFA</span>
      </div>
      <div class="footer-links">
        <a href="{html.escape(github_url)}" target="_blank" rel="noopener noreferrer">Código aberto no GitHub</a>
        <span class="footer-sep">·</span>
        <a href="{html.escape(github_url)}/blob/main/README.md" target="_blank" rel="noopener noreferrer">Metodologia</a>
        <span class="footer-sep">·</span>
        <a href="https://github.com/ElderGil" target="_blank" rel="noopener noreferrer">Elder Gil</a>
      </div>
      <p class="footer-disclaimer">Os dados são gerados automaticamente a partir de fontes oficiais da FIFA e atualizados diariamente. As probabilidades refletem o modelo <em>{html.escape(model_version)}</em> e não constituem aconselhamento de apostas. &copy; 2026 Elder Gil.</p>
    </div>
  </footer>
  <div class="panel-scrim" data-close-panel></div>
  <aside class="team-panel" id="team-panel" aria-hidden="true" aria-label="Detalhes da seleção">
    <button class="panel-close" type="button" data-close-panel aria-label="Fechar">✕</button>
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
      <div><dt>Força</dt><dd data-panel-strength></dd></div>
      <div><dt>Oitavas</dt><dd data-panel-round-of-32></dd></div>
      <div><dt>Final</dt><dd data-panel-final></dd></div>
    </dl>
    <p class="panel-summary" data-panel-summary></p>
    <h3>Indicadores do modelo</h3>
    <div class="pillar-list" data-panel-drivers></div>
    <h3>Pilares usados</h3>
    <div class="pillar-list" data-panel-used></div>
    <h3>Pilares excluídos</h3>
    <div class="pillar-list" data-panel-excluded></div>
    <h3>Benchmarks</h3>
    <div class="pillar-list" data-panel-benchmarks></div>
  </aside>
  <button class="share-fab" id="share-btn" type="button" aria-label="Compartilhar previsão">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
    <span>Compartilhar</span>
  </button>
  <div class="share-toast" id="share-toast" aria-live="polite"></div>
  <script id="forecast-data" type="application/json">{data}</script>
  <script src="app.js"></script>
</body>
</html>
"""
    (target / "index.html").write_text(markup, encoding="utf-8")
    (target / "styles.css").write_text(_styles(), encoding="utf-8")
    (target / "app.js").write_text(_script(), encoding="utf-8")


def _format_date_friendly(iso_str: str) -> str:
    """Converte '2026-06-18T17:48:28.214710+00:00' em '18/06/2026 às 17:48 UTC'."""
    try:
        date_part, time_part = iso_str[:19].split("T")
        y, m, d = date_part.split("-")
        h, mi, _ = time_part.split(":")
        return f"{d}/{m}/{y} às {h}:{mi} UTC"
    except Exception:
        return iso_str


def _render_media_favorites() -> str:
    """Gera a seção HTML com os favoritos das mídias."""
    cols = ""
    for source_data in _MEDIA_FAVORITES:
        rows = ""
        for team in source_data["teams"]:
            rows += (
                f'<li class="media-fav-row">'
                f'<span class="media-fav-rank">#{team["rank"]}</span>'
                f'<span class="media-fav-flag">{html.escape(team["flag"])}</span>'
                f'<span class="media-fav-name">{html.escape(team["name"])}</span>'
                f"</li>"
            )
        note_html = ""
        if source_data.get("note"):
            note_html = f'<p class="media-source-note">{html.escape(source_data["note"])}</p>'
        cols += (
            f'<div class="media-fav-col">'
            f'<div class="media-fav-header">'
            f'<strong class="media-fav-source">{html.escape(source_data["source"])}</strong>'
            f'<a href="{html.escape(source_data["source_url"])}" target="_blank" rel="noopener noreferrer" class="media-fav-link">ver fonte ↗</a>'
            f'</div>'
            f'<p class="media-fav-date">Coletado em {html.escape(source_data["collected_at"])}</p>'
            f'{note_html}'
            f'<ol class="media-fav-list">{rows}</ol>'
            f"</div>"
        )
    return (
        '<section class="media-favorites">'
        '<div class="section-heading">'
        '<div>'
        '<h2>O que dizem as mídias e casas de apostas</h2>'
        '<p class="section-sub">Favoritos apontados por fontes externas — dado fixo, não atualiza automaticamente</p>'
        '</div>'
        '</div>'
        f'<div class="media-fav-grid">{cols}</div>'
        "</section>"
    )


def _copy_site_assets(target: Path) -> None:
    assets_source = Path(__file__).with_name("assets")
    hero_source = assets_source / "hero-stadium.png"
    if not hero_source.exists():
        return
    assets_target = target / "assets"
    assets_target.mkdir(parents=True, exist_ok=True)
    copyfile(hero_source, assets_target / "hero-stadium.png")


def _team_card(team: dict[str, Any], *, large: bool) -> str:
    klass = "team-card large" if large else "team-card"
    display_name = _display_name(team)
    return (
        f'<button class="{klass}" type="button" data-team="{html.escape(team["team"])}">'
        f'<span class="rank">#{team["rank"]}</span>'
        f"{_flag_badge(team)}"
        f'<span class="name">{html.escape(display_name)}</span>'
        f"<strong>{team['champion_probability']:.1%}</strong>"
        "</button>"
    )


def _ranking_row(team: dict[str, Any]) -> str:
    display_name = _display_name(team)
    return (
        f'<li><button type="button" data-team="{html.escape(team["team"])}">'
        f'<span class="top-team"><span>#{team["rank"]}</span>{_flag_badge(team)}'
        f'<span>{html.escape(display_name)}</span></span>'
        f"<strong>{team['champion_probability']:.1%}</strong></button></li>"
    )


def _enrich_display_payload(latest: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(latest)
    teams = []
    for team in latest.get("teams", []):
        item = dict(team)
        item["display_name"] = display_team_name(str(item.get("team", "")))
        item["flag_emoji"] = flag_emoji(str(item.get("flag", "")))
        teams.append(item)
    enriched["teams"] = teams
    return enriched


def _display_name(team: dict[str, Any]) -> str:
    return str(team.get("display_name") or display_team_name(str(team.get("team", ""))))


def _flag_badge(team: dict[str, Any]) -> str:
    code = str(team.get("flag") or "")
    emoji = str(team.get("flag_emoji") or flag_emoji(code))
    label = " ".join(part for part in (emoji, code) if part)
    return (
        f'<span class="flag-badge" aria-label="{html.escape(label)}">'
        f'<span class="flag-emoji" aria-hidden="true">{html.escape(emoji)}</span>'
        f'<span class="flag-code">{html.escape(code)}</span>'
        "</span>"
    )


def _styles() -> str:
    return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap');
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #f4f1ea; color: #17211b; }
button, a { font: inherit; }

/* ── Header ── */
.site-header { min-height: 64px; display:flex; align-items:center; justify-content:space-between; padding:16px 28px; background:#fffaf0; border-bottom:1px solid #ded8ca; position:sticky; top:0; z-index:10; gap:12px; }
.site-title { font-size:18px; font-weight:900; letter-spacing:-0.3px; }
.gh-link { display:inline-flex; align-items:center; gap:7px; color:#17211b; font-weight:800; text-decoration:none; border:1.5px solid #d8d0bf; border-radius:8px; padding:7px 13px; transition:background .15s, border-color .15s; }
.gh-link:hover { background:#f4c430; border-color:#f4c430; }
.gh-icon { width:18px; height:18px; flex-shrink:0; }

/* ── Hero ── */
.hero { min-height: calc(100vh - 64px); padding: 34px 28px 28px; display:grid; grid-template-columns: minmax(280px, 0.72fr) minmax(420px, 1.28fr); gap:28px; align-items:center; color:#fffaf0; position:relative; overflow:hidden; isolation:isolate; background:linear-gradient(90deg, rgba(6,28,21,.92) 0%, rgba(6,28,21,.72) 42%, rgba(6,28,21,.48) 100%), linear-gradient(180deg, rgba(4,12,24,.72) 0%, rgba(4,12,24,.12) 46%, rgba(6,28,21,.82) 100%), url("assets/hero-stadium.png") center center / cover no-repeat; box-shadow:inset 0 -120px 120px rgba(6,28,21,.52); }
.hero > * { position:relative; z-index:1; }
.hero-copy { display:grid; gap:22px; align-content:center; text-shadow:0 3px 18px rgba(0,0,0,.68); }
h1 { font-size: 58px; line-height:1; margin:0; max-width: 680px; color:#fffaf0; text-shadow:0 5px 24px rgba(0,0,0,.78); }

/* ── Run Stamp ── */
.run-stamp { display:grid; gap:3px; }
.run-stamp-label { font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:#a8c5b4; }
.run-stamp-value { font-size:16px; font-weight:900; color:#f7e9b5; }
.run-stamp-sub { font-size:12px; color:#a8c5b4; }

/* ── Run Meta ── */
.run-meta { display:flex; flex-wrap:wrap; gap:10px; }
.run-meta-version, .run-meta-calib { display:inline-flex; align-items:center; gap:7px; border:1px solid rgba(247,233,181,.55); border-radius:999px; padding:7px 14px; color:#fffaf0; background:rgba(6,28,21,.6); backdrop-filter:blur(4px); font-size:13px; }
.run-meta-version strong { font-weight:900; }
.run-meta-calib { border-color:rgba(251,191,36,.42); background:rgba(120,53,15,.35); font-size:12px; }
.run-meta-icon { font-size:15px; }

/* ── Top Board ── */
.top-board { display:grid; gap:14px; }
.podium { display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:14px; align-items:stretch; }
.team-card { min-height:142px; border:1px solid #d8d0bf; background:#fffdf8; color:#17211b; border-radius:10px; padding:18px; display:grid; gap:8px; text-align:left; cursor:pointer; box-shadow:0 8px 18px rgba(23,33,27,.08); transition:transform .14s, box-shadow .14s; }
.team-card:hover { transform:translateY(-3px); box-shadow:0 14px 28px rgba(23,33,27,.13); }
.team-card:focus-visible, .top-list button:focus-visible { outline:3px solid #f4c430; outline-offset:2px; }
.team-card.large { min-height:230px; align-content:end; border-color:#f4c430; color:#fffaf0; background:linear-gradient(155deg,#1e5f45,#8b1e22); }
.team-card .name { font-weight:800; font-size:20px; overflow-wrap:anywhere; }
.team-card strong { font-size:28px; }
.team-card.large strong { font-size:34px; }
.flag-badge { min-width:54px; min-height:42px; width:max-content; display:inline-grid; grid-template-columns:auto auto; align-items:center; justify-content:center; gap:6px; border-radius:4px; padding:5px 8px; background:#f4c430; color:#17211b; font-weight:900; }
.flag-emoji { font-size:24px; line-height:1; filter:saturate(1.08); }
.flag-code { font-size:12px; letter-spacing:0; }
.rank { color:#6e786f; font-weight:800; }
.team-card.large .rank { color:#f7e9b5; }
.top-list { list-style:none; padding:0; margin:0; display:grid; gap:10px; }
.top-list li { margin:0; }
.top-list button { width:100%; min-height:56px; display:flex; align-items:center; justify-content:space-between; gap:12px; border:1px solid rgba(216,208,191,.5); background:rgba(255,253,248,.88); color:#17211b; padding:10px 14px; border-radius:10px; cursor:pointer; transition:background .13s; backdrop-filter:blur(4px); }
.top-list button:hover { background:rgba(255,253,248,1); }
.top-team { display:flex; align-items:center; gap:10px; min-width:0; font-weight:800; }
.top-team > span:last-child { overflow-wrap:anywhere; }
.top-list strong { color:#8b1e22; }

/* ── Media Favorites ── */
.media-favorites { padding: 40px 28px; background:#fffaf0; border-top:1px solid #ded8ca; }
.section-sub { color:#59645c; font-size:14px; margin:4px 0 0; }
.media-fav-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:20px; margin-top:22px; }
.media-fav-col { background:#fff; border:1px solid #e2ddd4; border-radius:12px; padding:20px; box-shadow:0 4px 12px rgba(23,33,27,.06); }
.media-fav-header { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:4px; }
.media-fav-source { font-size:15px; font-weight:900; color:#17211b; }
.media-fav-link { font-size:12px; color:#b91c1c; font-weight:700; text-decoration:none; white-space:nowrap; }
.media-fav-link:hover { text-decoration:underline; }
.media-fav-date { font-size:12px; color:#8a9490; margin:0 0 10px; }
.media-source-note { font-size:12px; color:#59645c; margin:0 0 10px; line-height:1.5; background:#f4f1ea; border-radius:6px; padding:8px 10px; }
.media-fav-list { list-style:none; margin:0; padding:0; display:grid; gap:6px; }
.media-fav-row { display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid #f0ece4; }
.media-fav-row:last-child { border-bottom:none; }
.media-fav-rank { font-size:13px; font-weight:900; color:#8a9490; min-width:24px; }
.media-fav-flag { font-size:22px; line-height:1; }
.media-fav-name { font-size:14px; font-weight:800; color:#17211b; }

/* ── All Teams ── */
.all-teams { padding: 30px 28px 46px; }
.section-heading { display:flex; align-items:end; justify-content:space-between; gap:18px; margin-bottom:18px; }
.section-heading h2 { font-size:32px; margin:0; }
.section-heading p { margin:0; color:#59645c; font-weight:700; }
.team-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap:14px; }

/* ── Panel ── */
.panel-scrim { position:fixed; inset:0; background:rgba(17,30,24,.42); opacity:0; pointer-events:none; transition:opacity .18s ease; z-index:20; }
.team-panel { position:fixed; top:0; right:0; width:min(430px, 100vw); height:100vh; overflow:auto; transform:translateX(100%); transition:transform .2s ease; background:#fffdf8; color:#17211b; z-index:30; box-shadow:-24px 0 40px rgba(17,30,24,.22); padding:28px; }
body.panel-open .panel-scrim { opacity:1; pointer-events:auto; }
body.panel-open .team-panel { transform:translateX(0); }
.panel-close { position:absolute; top:16px; right:16px; width:42px; height:42px; border:1px solid #d8d0bf; border-radius:8px; background:#fffaf0; cursor:pointer; font-weight:900; font-size:16px; }
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

/* ── Share FAB ── */
.share-fab { position:fixed; bottom:28px; right:28px; display:inline-flex; align-items:center; gap:9px; background:#1e5f45; color:#f7e9b5; border:none; border-radius:999px; padding:14px 22px; font-size:15px; font-weight:800; cursor:pointer; box-shadow:0 8px 24px rgba(30,95,69,.4); transition:transform .15s, box-shadow .15s; z-index:15; }
.share-fab:hover { transform:translateY(-3px); box-shadow:0 14px 32px rgba(30,95,69,.5); }
.share-fab svg { width:20px; height:20px; flex-shrink:0; }
.share-toast { position:fixed; bottom:90px; right:28px; background:#17211b; color:#f7e9b5; border-radius:10px; padding:12px 18px; font-size:14px; font-weight:700; opacity:0; pointer-events:none; transition:opacity .25s; z-index:16; max-width:260px; }
.share-toast.visible { opacity:1; }

/* ── Footer ── */
.site-footer { background:#17211b; color:#a8c5b4; padding:36px 28px; }
.footer-inner { max-width:960px; margin:0 auto; display:grid; gap:16px; }
.footer-brand { display:flex; flex-direction:column; gap:4px; }
.footer-brand strong { color:#f7e9b5; font-size:16px; font-weight:900; }
.footer-brand span { font-size:13px; }
.footer-links { display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-size:13px; }
.footer-links a { color:#f4c430; font-weight:700; text-decoration:none; }
.footer-links a:hover { text-decoration:underline; }
.footer-sep { color:#4a5c50; }
.footer-disclaimer { font-size:11px; color:#4a5c50; line-height:1.6; margin:0; border-top:1px solid #2a3d31; padding-top:16px; }

/* ── Responsive ── */
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
  .share-fab { bottom:18px; right:18px; padding:12px 18px; font-size:14px; }
  .media-favorites { padding:28px 18px; }
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
  const missing = pillar.missing_teams == null ? '-' : pillar.missing_teams;
  meta.textContent = `${percent(pillar.coverage)} cobertura | faltantes: ${missing} | ${pillar.reason || 'coverage_ok'} | ${pillar.source || 'fonte pendente'}`;
  item.append(title, meta);
  return item;
}

function renderDrivers(keys) {
  const target = panel.querySelector('[data-panel-drivers]');
  target.replaceChildren();
  (keys || []).forEach((driver) => {
    const item = document.createElement('div');
    item.className = 'pillar-item';
    item.textContent = driver;
    target.append(item);
  });
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
  const advancement = team.advancement_probabilities || {};
  setText('[data-panel-rank]', `#${team.rank}`);
  const flagTarget = panel.querySelector('[data-panel-flag]');
  if (flagTarget) flagTarget.textContent = [team.flag_emoji, team.flag].filter(Boolean).join(' ');
  setText('[data-panel-team]', team.display_name || team.team);
  setText('[data-panel-probability]', percent(team.champion_probability));
  setText('[data-panel-group]', team.group);
  setText('[data-panel-points]', signal.points);
  setText('[data-panel-goal-difference]', signal.goal_difference);
  setText('[data-panel-strength]', number(team.strength));
  setText('[data-panel-round-of-32]', percent(advancement.round_of_32));
  setText('[data-panel-final]', percent(advancement.final));
  setText('[data-panel-summary]', team.summary);
  renderDrivers(team.drivers || []);
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

// Share FAB
const shareBtn = document.getElementById('share-btn');
const shareToast = document.getElementById('share-toast');
let toastTimer = null;

function showToast(msg) {
  shareToast.textContent = msg;
  shareToast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => shareToast.classList.remove('visible'), 3000);
}

if (shareBtn) {
  shareBtn.addEventListener('click', async () => {
    const shareData = {
      title: 'Copa 2026 AI Forecast',
      text: '⚽ Veja as previsões de título da Copa 2026 geradas por IA com dados oficiais da FIFA!',
      url: window.location.href,
    };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        showToast('✅ Link copiado! Compartilhe com um amigo 🏆');
      }
    } catch {
      await navigator.clipboard.writeText(window.location.href).catch(() => {});
      showToast('✅ Link copiado!');
    }
  });
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
