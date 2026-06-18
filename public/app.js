
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

document.addEventListener('click', (event) => {
  const card = event.target.closest('[data-team]');
  if (card) openPanel(card.dataset.team);
  if (event.target.closest('[data-close-panel]')) closePanel();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closePanel();
});
