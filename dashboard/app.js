"use strict";

// Dashboard over dashboard/data/tech_postings.csv, written by `jobmarket export`.
// Every number is computed in the browser from that file, with the same rules
// as the SQL report: medians use linear interpolation (DuckDB's quantile_cont)
// and are rounded to the nearest $100.

const DATA_URL = "data/tech_postings.csv";
const REGIONS = ["Toronto Region", "Rest of Canada"];
const MIN_SALARIES = 10;
const SVG_NS = "http://www.w3.org/2000/svg";

const state = { rows: [], months: [], families: [], period: 12, family: "", source: "" };

// ---------------------------------------------------------------- data

function parseCsv(text) {
  const records = [];
  let record = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        field += '"';
        i++;
      } else if (c === '"') {
        quoted = false;
      } else {
        field += c;
      }
    } else if (c === '"') {
      quoted = true;
    } else if (c === ",") {
      record.push(field);
      field = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      record.push(field);
      records.push(record);
      record = [];
      field = "";
    } else {
      field += c;
    }
  }
  if (field !== "" || record.length) {
    record.push(field);
    records.push(record);
  }
  return records;
}

function toRows(records) {
  const [header, ...body] = records;
  const at = Object.fromEntries(header.map((name, i) => [name, i]));
  return body
    .filter((values) => values.length === header.length)
    .map((values) => ({
      month: values[at.month],
      region: values[at.region],
      family: values[at.family],
      occupation: values[at.occupation],
      source: values[at.source],
      experience: values[at.experience],
      experienceRank: values[at.experience_rank] === "" ? null : Number(values[at.experience_rank]),
      salary: values[at.annual_salary] === "" ? null : Number(values[at.annual_salary]),
    }));
}

function quantile(sorted, p) {
  const h = (sorted.length - 1) * p;
  const lo = Math.floor(h);
  const hi = Math.ceil(h);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (h - lo);
}

function salaryStats(rows) {
  const salaries = rows
    .map((row) => row.salary)
    .filter((salary) => salary !== null)
    .sort((a, b) => a - b);
  if (salaries.length < MIN_SALARIES) return { n: salaries.length, median: null };
  const round = (value) => Math.round(value / 100) * 100;
  return {
    n: salaries.length,
    median: round(quantile(salaries, 0.5)),
    p25: round(quantile(salaries, 0.25)),
    p75: round(quantile(salaries, 0.75)),
  };
}

function groupBy(rows, key) {
  const groups = new Map();
  for (const row of rows) {
    const value = key(row);
    if (!groups.has(value)) groups.set(value, []);
    groups.get(value).push(row);
  }
  return groups;
}

function byRegion(rows) {
  return REGIONS.map((region) => rows.filter((row) => row.region === region));
}

// ---------------------------------------------------------------- formatting

const integer = new Intl.NumberFormat("en-CA");

function money(value) {
  return value === null ? "–" : `$${integer.format(value)}`;
}

function compactMoney(value) {
  return value === 0 ? "$0" : `$${integer.format(value / 1000)}k`;
}

function monthLabel(month, style = "short") {
  const [year, m] = month.split("-").map(Number);
  const date = new Date(year, m - 1, 1);
  return date.toLocaleString("en-CA", { month: style, year: "numeric" });
}

function niceTicks(max, count) {
  if (max <= 0) return [0, 1];
  const raw = max / count;
  const power = 10 ** Math.floor(Math.log10(raw));
  const fraction = raw / power;
  // 2.5 only for powers of ten from 10 up, so integer counts get integer ticks.
  const quarter = power >= 10 && fraction <= 2.5 ? 2.5 : null;
  const step = (fraction <= 1 ? 1 : fraction <= 2 ? 2 : quarter ?? (fraction <= 5 ? 5 : 10)) * power;
  const ticks = [];
  for (let value = 0; value < max + step - 1e-9; value += step) ticks.push(value);
  return ticks;
}

// ---------------------------------------------------------------- DOM helpers

function svgElement(tag, attributes = {}, parent = null) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
  if (parent) parent.appendChild(element);
  return element;
}

function svgText(parent, x, y, text, attributes = {}) {
  const element = svgElement("text", { x, y, ...attributes }, parent);
  element.textContent = text;
  return element;
}

function htmlTable(container, headers, rows, numeric) {
  const table = document.createElement("table");
  const head = table.createTHead().insertRow();
  headers.forEach((header, i) => {
    const cell = document.createElement("th");
    cell.textContent = header;
    if (numeric[i]) cell.className = "num";
    head.appendChild(cell);
  });
  const body = table.createTBody();
  for (const values of rows) {
    const row = body.insertRow();
    values.forEach((value, i) => {
      const cell = row.insertCell();
      cell.textContent = value;
      if (numeric[i]) cell.className = "num";
    });
  }
  container.replaceChildren(table);
}

function emptyMessage(container, text) {
  const message = document.createElement("p");
  message.className = "empty";
  message.textContent = text;
  container.replaceChildren(message);
}

// ---------------------------------------------------------------- tooltip

const tooltip = () => document.getElementById("tooltip");

function showTooltip(x, y, title, lines) {
  const box = tooltip();
  const heading = document.createElement("div");
  heading.className = "tt-title";
  heading.textContent = title;
  const rows = lines.map(({ value, label, key }) => {
    const row = document.createElement("div");
    row.className = "tt-row";
    const swatch = document.createElement("span");
    swatch.className = `key line ${key}`;
    const strong = document.createElement("span");
    strong.className = "tt-value";
    strong.textContent = value;
    const text = document.createElement("span");
    text.className = "tt-label";
    text.textContent = label;
    row.append(swatch, strong, text);
    return row;
  });
  box.replaceChildren(heading, ...rows);
  box.hidden = false;
  const { width, height } = box.getBoundingClientRect();
  const left = Math.min(x + 14, window.innerWidth - width - 8);
  const top = y + 14 + height > window.innerHeight ? y - height - 14 : y + 14;
  box.style.left = `${Math.max(8, left)}px`;
  box.style.top = `${Math.max(8, top)}px`;
}

function hideTooltip() {
  tooltip().hidden = true;
}

function anchorOf(element) {
  const rect = element.getBoundingClientRect();
  return [rect.left + rect.width / 2, rect.top + rect.height / 2];
}

// ---------------------------------------------------------------- charts

function renderTrend(rows, months) {
  const container = document.getElementById("trend");
  const index = new Map(months.map((month, i) => [month, i]));
  const counts = REGIONS.map(() => months.map(() => 0));
  for (const row of rows) counts[REGIONS.indexOf(row.region)][index.get(row.month)]++;

  htmlTable(
    document.getElementById("trend-table"),
    ["Month", ...REGIONS],
    months.map((month, i) => [
      monthLabel(month, "long"),
      integer.format(counts[0][i]),
      integer.format(counts[1][i]),
    ]),
    [false, true, true],
  );
  if (!rows.length) return emptyMessage(container, "No postings match these filters.");

  const width = container.clientWidth;
  const height = 240;
  const margin = { top: 10, right: 12, bottom: 26, left: 44 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const ticks = niceTicks(Math.max(...counts.flat()), 4);
  const top = ticks[ticks.length - 1];
  const step = months.length > 1 ? innerWidth / (months.length - 1) : 0;
  const x = (i) => margin.left + (months.length > 1 ? i * step : innerWidth / 2);
  const y = (value) => margin.top + innerHeight * (1 - value / top);

  const svg = svgElement("svg", {
    width,
    height,
    viewBox: `0 0 ${width} ${height}`,
    tabindex: 0,
    role: "img",
    "aria-label": `Postings per month, ${REGIONS.join(" and ")}. Use the arrow keys to read each month.`,
  });
  for (const value of ticks) {
    const cls = value === 0 ? "axis" : "grid";
    svgElement("line", { class: cls, x1: margin.left, x2: width - margin.right, y1: y(value), y2: y(value) }, svg);
    svgText(svg, margin.left - 8, y(value) + 4, integer.format(value), { class: "tick", "text-anchor": "end" });
  }
  const every = innerWidth < 420 ? 3 : innerWidth < 640 ? 2 : 1;
  months.forEach((month, i) => {
    if ((months.length - 1 - i) % every) return;
    const [year, m] = month.split("-");
    const label = i === 0 || m === "01" ? `${monthLabel(month).split(" ")[0]} ${year}` : monthLabel(month).split(" ")[0];
    svgText(svg, x(i), height - 6, label, { class: "tick", "text-anchor": "middle" });
  });

  const crosshair = svgElement("line", { class: "crosshair", y1: margin.top, y2: margin.top + innerHeight, visibility: "hidden" }, svg);
  const focusDots = [];
  counts.forEach((series, s) => {
    const points = series.map((value, i) => `${x(i)},${y(value)}`).join(" ");
    svgElement("polyline", { class: `series-line s${s + 1}`, points }, svg);
    const last = series.length - 1;
    svgElement("circle", { class: `dot fill-${s + 1}`, cx: x(last), cy: y(series[last]), r: 4 }, svg);
    focusDots.push(svgElement("circle", { class: `dot fill-${s + 1}`, r: 4, visibility: "hidden" }, svg));
  });

  let current = months.length - 1;
  const show = (i, clientX, clientY) => {
    current = i;
    crosshair.setAttribute("x1", x(i));
    crosshair.setAttribute("x2", x(i));
    crosshair.setAttribute("visibility", "visible");
    focusDots.forEach((dot, s) => {
      dot.setAttribute("cx", x(i));
      dot.setAttribute("cy", y(counts[s][i]));
      dot.setAttribute("visibility", "visible");
    });
    const lines = REGIONS.map((region, s) => ({
      value: integer.format(counts[s][i]),
      label: region,
      key: `s${s + 1}`,
    }));
    if (clientX === undefined) {
      const rect = svg.getBoundingClientRect();
      clientX = rect.left + x(i);
      clientY = rect.top + margin.top;
    }
    showTooltip(clientX, clientY, monthLabel(months[i], "long"), lines);
  };
  const hide = () => {
    crosshair.setAttribute("visibility", "hidden");
    focusDots.forEach((dot) => dot.setAttribute("visibility", "hidden"));
    hideTooltip();
  };
  const overlay = svgElement("rect", { class: "hit", x: margin.left - step / 2, y: 0, width: innerWidth + step, height }, svg);
  overlay.addEventListener("pointermove", (event) => {
    const px = event.clientX - svg.getBoundingClientRect().left;
    const i = step ? Math.round((px - margin.left) / step) : 0;
    show(Math.max(0, Math.min(months.length - 1, i)), event.clientX, event.clientY);
  });
  overlay.addEventListener("pointerleave", hide);
  svg.addEventListener("focus", () => show(current));
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      const next = current + (event.key === "ArrowRight" ? 1 : -1);
      show(Math.max(0, Math.min(months.length - 1, next)));
    } else if (event.key === "Escape") {
      hide();
    }
  });
  container.replaceChildren(svg);
}

// Horizontal bars, one pair (Toronto Region, Rest of Canada) per group.
// groups: [{ label, stats: [stats per region] }]
function renderPairedBars(container, groups, unit) {
  if (!groups.length) return emptyMessage(container, "No postings match these filters.");
  const width = container.clientWidth;
  const margin = { top: 4, right: 76, bottom: 24, left: 4 };
  const labelHeight = 20;
  const bar = 12;
  const gap = 2;
  const after = 14;
  const groupHeight = labelHeight + 2 * bar + gap + after;
  const height = margin.top + groups.length * groupHeight + margin.bottom;
  const innerWidth = width - margin.left - margin.right;
  const medians = groups.flatMap((group) => group.stats.map((stats) => stats.median ?? 0));
  const ticks = niceTicks(Math.max(...medians, 1), innerWidth < 360 ? 3 : 5);
  const top = ticks[ticks.length - 1];
  const x = (value) => margin.left + (innerWidth * value) / top;
  const plotBottom = height - margin.bottom;

  const svg = svgElement("svg", { width, height, viewBox: `0 0 ${width} ${height}`, role: "group" });
  for (const value of ticks) {
    svgElement("line", { class: value === 0 ? "axis" : "grid", x1: x(value), x2: x(value), y1: margin.top, y2: plotBottom }, svg);
    svgText(svg, x(value), height - 6, compactMoney(value), { class: "tick", "text-anchor": "middle" });
  }

  groups.forEach((group, g) => {
    const top = margin.top + g * groupHeight;
    const row = svgElement("g", { class: "row" }, svg);
    svgElement("rect", { class: "wash", x: 0, y: top, width, height: groupHeight - after / 2, rx: 4 }, row);
    svgText(row, margin.left, top + 14, group.label, { class: "label" });
    group.stats.forEach((stats, s) => {
      const y = top + labelHeight + s * (bar + gap);
      if (stats.median === null) {
        svgText(row, x(0) + 6, y + bar - 2, `fewer than ${MIN_SALARIES} salaries`, { class: "note" });
        return;
      }
      const w = Math.max(1, x(stats.median) - x(0));
      const r = Math.min(4, w, bar / 2);
      const x0 = x(0);
      const d = `M${x0},${y}H${x0 + w - r}A${r},${r} 0 0 1 ${x0 + w},${y + r}V${y + bar - r}A${r},${r} 0 0 1 ${x0 + w - r},${y + bar}H${x0}Z`;
      svgElement("path", { class: `fill-${s + 1}`, d }, row);
      svgText(row, x0 + w + 6, y + bar - 2, money(stats.median), { class: "value" });
    });

    const describe = (stats) =>
      stats.median === null
        ? `fewer than ${MIN_SALARIES} salaries`
        : `${money(stats.median)} from ${integer.format(stats.n)} ${unit}`;
    const hit = svgElement("rect", {
      class: "hit",
      x: 0,
      y: top,
      width,
      height: groupHeight - after / 2,
      tabindex: 0,
      role: "img",
      "aria-label": `${group.label}: ${REGIONS.map((region, s) => `${region} ${describe(group.stats[s])}`).join("; ")}`,
    }, row);
    const lines = () =>
      group.stats.map((stats, s) => ({
        value: money(stats.median),
        label:
          stats.median === null
            ? `${REGIONS[s]}, fewer than ${MIN_SALARIES} salaries`
            : `${REGIONS[s]}, ${integer.format(stats.n)} ${unit}, middle half ${compactMoney(stats.p25)}–${compactMoney(stats.p75)}`,
        key: `s${s + 1}`,
      }));
    const activate = (clientX, clientY) => {
      row.classList.add("active");
      showTooltip(clientX, clientY, group.label, lines());
    };
    const deactivate = () => {
      row.classList.remove("active");
      hideTooltip();
    };
    hit.addEventListener("pointermove", (event) => activate(event.clientX, event.clientY));
    hit.addEventListener("pointerleave", deactivate);
    hit.addEventListener("focus", () => activate(...anchorOf(hit)));
    hit.addEventListener("blur", deactivate);
  });
  container.replaceChildren(svg);
}

function pairedTable(container, firstHeader, groups) {
  htmlTable(
    container,
    [firstHeader, "Toronto median", "Toronto salaries", "Rest of Canada median", "Rest of Canada salaries"],
    groups.map((group) => [
      group.label,
      money(group.stats[0].median),
      integer.format(group.stats[0].n),
      money(group.stats[1].median),
      integer.format(group.stats[1].n),
    ]),
    [false, true, true, true, true],
  );
}

function renderSalary(rows) {
  const key = state.family ? (row) => row.occupation : (row) => row.family;
  const groups = [...groupBy(rows, key)]
    .map(([label, members]) => ({
      label,
      count: members.filter((row) => row.region === REGIONS[0]).length,
      stats: byRegion(members).map(salaryStats),
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
  document.getElementById("salary-title").textContent = state.family
    ? `Median annual salary by occupation: ${state.family}`
    : "Median annual salary by family";
  renderPairedBars(document.getElementById("salary"), groups, "salaries");
  pairedTable(document.getElementById("salary-table"), state.family ? "Occupation" : "Family", groups);
}

function renderExperience(rows) {
  const container = document.getElementById("experience");
  const table = document.getElementById("experience-table");
  if (state.source === "External job board") {
    emptyMessage(container, "External job boards do not report experience. Choose all sources or direct employer postings.");
    table.replaceChildren();
    return;
  }
  const direct = rows.filter((row) => row.source === "Direct employer" && row.experienceRank !== null);
  const groups = [...groupBy(direct, (row) => row.experience)]
    .map(([label, members]) => ({
      label,
      rank: members[0].experienceRank,
      stats: byRegion(members).map(salaryStats),
    }))
    .sort((a, b) => a.rank - b.rank);
  renderPairedBars(container, groups, "salaries");
  pairedTable(table, "Experience", groups);
}

function renderOccupations(rows) {
  const toronto = rows.filter((row) => row.region === REGIONS[0]);
  const groups = [...groupBy(rows, (row) => row.occupation)]
    .map(([occupation, members]) => {
      const [here, rest] = byRegion(members);
      return { occupation, family: members[0].family, count: here.length, here: salaryStats(here), rest: salaryStats(rest) };
    })
    .filter((group) => group.count > 0)
    .sort((a, b) => b.count - a.count || a.occupation.localeCompare(b.occupation));
  const container = document.getElementById("occupations");
  if (!groups.length) return emptyMessage(container, "No Toronto postings match these filters.");
  htmlTable(
    container,
    ["Occupation", "Family", "Toronto postings", "Share", "Toronto median", "Rest of Canada median"],
    groups.map((group) => [
      group.occupation,
      group.family,
      integer.format(group.count),
      `${((100 * group.count) / toronto.length).toFixed(1)}%`,
      money(group.here.median),
      money(group.rest.median),
    ]),
    [false, false, true, true, true, true],
  );
}

function renderTiles(rows) {
  const [toronto, rest] = byRegion(rows);
  const set = (id, text) => {
    document.getElementById(id).textContent = text;
  };
  set("tile-toronto-count", integer.format(toronto.length));
  set("tile-rest-count", integer.format(rest.length));
  [
    ["toronto", toronto],
    ["rest", rest],
  ].forEach(([name, members]) => {
    const stats = salaryStats(members);
    set(`tile-${name}-salary`, money(stats.median));
    set(`tile-${name}-salary-sub`, stats.median === null ? `fewer than ${MIN_SALARIES} salaries` : `from ${integer.format(stats.n)} salaries`);
    const share = members.length ? Math.round((100 * stats.n) / members.length) : 0;
    set(`tile-${name}-count-sub`, `${share}% state a salary`);
  });
}

// ---------------------------------------------------------------- page

function selectedMonths() {
  return state.months.slice(-state.period);
}

function render() {
  const months = selectedMonths();
  const inPeriod = new Set(months);
  const rows = state.rows.filter(
    (row) =>
      inPeriod.has(row.month) &&
      (!state.family || row.family === state.family) &&
      (!state.source || row.source === state.source),
  );
  const range = `${monthLabel(months[0])} – ${monthLabel(months[months.length - 1])}`;
  document.getElementById("period-label").textContent = `Job Bank open data · ${range}`;
  document.getElementById("status").textContent =
    `${integer.format(rows.length)} tech postings, ${range}` +
    (state.family ? `, ${state.family}` : "") +
    (state.source ? `, ${state.source.toLowerCase()} postings` : "") +
    ".";
  document.getElementById("template-note").hidden = state.source === "Direct employer";
  renderTiles(rows);
  renderTrend(rows, months);
  renderSalary(rows);
  renderExperience(rows);
  renderOccupations(rows);
}

// Filters live in the URL (?period=6&family=Data&source=Direct+employer), so a
// view can be shared as a link.
function readFilters() {
  const params = new URLSearchParams(window.location.search);
  const controls = {
    period: document.getElementById("period"),
    family: document.getElementById("family"),
    source: document.getElementById("source"),
  };
  for (const [name, control] of Object.entries(controls)) {
    const value = params.get(name);
    if (value !== null && [...control.options].some((option) => option.value === value)) {
      control.value = value;
    }
  }
  state.period = Number(controls.period.value);
  state.family = controls.family.value;
  state.source = controls.source.value;
}

function writeFilters() {
  const params = new URLSearchParams();
  if (state.period !== 12) params.set("period", state.period);
  if (state.family) params.set("family", state.family);
  if (state.source) params.set("source", state.source);
  const query = params.toString();
  window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
}

function setUpFilters() {
  const family = document.getElementById("family");
  for (const name of state.families) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    family.appendChild(option);
  }
  readFilters();
  document.getElementById("filters").addEventListener("change", () => {
    readFilters();
    writeFilters();
    hideTooltip();
    render();
  });
}

async function main() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.rows = toRows(parseCsv(await response.text()));
  } catch (error) {
    document.getElementById("status").textContent = `Could not load the data (${error.message}).`;
    return;
  }
  state.months = [...new Set(state.rows.map((row) => row.month))].sort();
  const familyCounts = groupBy(state.rows, (row) => row.family);
  state.families = [...familyCounts.keys()].sort(
    (a, b) => familyCounts.get(b).length - familyCounts.get(a).length,
  );
  setUpFilters();
  render();

  let width = document.querySelector("main").clientWidth;
  let pending = false;
  new ResizeObserver(() => {
    const next = document.querySelector("main").clientWidth;
    if (next === width || pending) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      width = document.querySelector("main").clientWidth;
      render();
    });
  }).observe(document.querySelector("main"));
}

main();
