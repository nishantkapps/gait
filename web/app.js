const $ = (id) => document.getElementById(id);

const SKIP = "";

/** @type {{ opensim_markers: string[], default_markers: Record<string,string>, default_average_markers: Record<string, {sources: string[]}> }} */
let setup = {
  opensim_markers: [],
  default_markers: {},
  default_average_markers: {},
};

/** @type {string[]} */
let sourceMarkers = [];

async function loadAppConfig() {
  const res = await fetch("app.config.json");
  return res.json();
}

async function loadTrialTemplate() {
  const res = await fetch("trial.template.yaml");
  return res.text();
}

async function loadMarkerSetup(apiBase) {
  const res = await fetch(`${apiBase}/api/marker_setup`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function buildYaml(template, form) {
  const height = Number(form.height_m.value);
  return template
    .replaceAll("__SUBJECT_ID__", form.subject_id.value.trim())
    .replaceAll("__MASS_KG__", String(Number(form.mass_kg.value)))
    .replaceAll("__HEIGHT_M__", Number.isFinite(height) ? String(height) : "null");
}

function pickCalC3d(files) {
  const c3ds = files.filter((f) => f.name.toLowerCase().endsWith(".c3d"));
  const cal = c3ds.find((f) => /cal/i.test(f.name));
  return cal || c3ds[0] || null;
}

function isLikelySurface(name) {
  if (/^\*\d+$/.test(name)) return false;
  if (/^(PEL|TRX|HED|LFE|RFE|LTI|RTI|LFO|RFO|LHU|RHU|LRA|RRA|LHN|RHN)[AOLP]$/.test(name)) {
    return false;
  }
  if (/(Angle|Force|Moment|Power|Bone|Joint|COM|Centre|Progress)/i.test(name)) {
    return false;
  }
  if (/^[LR](KD\d|KAX|TO[AOLP]|CL[LOP]|CLL)$/.test(name)) return false;
  return true;
}

function opensimOptionsHtml(selected) {
  const opts = [`<option value="${SKIP}">— skip —</option>`];
  for (const name of setup.opensim_markers) {
    const sel = name === selected ? " selected" : "";
    opts.push(`<option value="${escapeAttr(name)}"${sel}>${escapeHtml(name)}</option>`);
  }
  return opts.join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeAttr(s) {
  return escapeHtml(s).replaceAll('"', "&quot;");
}

function invertDefaultMap() {
  /** @type {Record<string, string>} */
  const bySrc = { ...setup.default_markers };
  return bySrc;
}

function renderMapTable() {
  const body = $("map-body");
  body.innerHTML = "";
  const defaults = invertDefaultMap();
  const rows = sourceMarkers.length
    ? sourceMarkers
    : Object.keys(defaults).sort();
  if (!rows.length) {
    body.innerHTML =
      '<tr><td colspan="2" class="empty">Load a Cal C3D to list source columns.</td></tr>';
    return;
  }
  for (const src of rows) {
    const tr = document.createElement("tr");
    const selected = defaults[src] || SKIP;
    tr.innerHTML = `
      <td><code class="src">${escapeHtml(src)}</code></td>
      <td>
        <select data-src="${escapeAttr(src)}" class="map-select">
          ${opensimOptionsHtml(selected)}
        </select>
      </td>`;
    body.appendChild(tr);
  }
}

function renderAverages() {
  const host = $("avg-body");
  host.innerHTML = "";
  const av = setup.default_average_markers || {};
  const keys = Object.keys(av).length
    ? Object.keys(av)
    : ["Head", "L.Wrist", "R.Wrist", "S2"];
  for (const dest of keys) {
    const sources = (av[dest] && av[dest].sources) || [];
    const wrap = document.createElement("label");
    wrap.innerHTML = `${escapeHtml(dest)}
      <input data-avg="${escapeAttr(dest)}" value="${escapeAttr(sources.join(", "))}"
        placeholder="SRC1, SRC2" />`;
    host.appendChild(wrap);
  }
}

function collectMarkerMapYaml() {
  /** @type {Record<string, string>} */
  const markers = {};
  for (const sel of document.querySelectorAll(".map-select")) {
    const src = sel.getAttribute("data-src");
    const dest = sel.value;
    if (src && dest) markers[src] = dest;
  }
  /** @type {Record<string, {sources: string[]}>} */
  const average_markers = {};
  for (const input of document.querySelectorAll("[data-avg]")) {
    const dest = input.getAttribute("data-avg");
    const sources = String(input.value)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (dest && sources.length) average_markers[dest] = { sources };
  }
  const lines = [
    "# Marker map from gait UI",
    "drop_unmapped: true",
    "",
    "markers:",
  ];
  for (const [src, dest] of Object.entries(markers).sort((a, b) =>
    a[1].localeCompare(b[1]) || a[0].localeCompare(b[0])
  )) {
    lines.push(`  ${src}: ${dest}`);
  }
  if (Object.keys(average_markers).length) {
    lines.push("", "average_markers:");
    for (const dest of Object.keys(average_markers).sort()) {
      const sources = average_markers[dest].sources;
      lines.push(`  ${dest}:`);
      lines.push(`    sources: [${sources.join(", ")}]`);
    }
  }
  return lines.join("\n") + "\n";
}

function wireFolder() {
  const input = $("folder-input");
  const label = $("drop-label");
  input.addEventListener("change", () => {
    const files = [...input.files];
    if (!files.length) {
      label.textContent = "Choose patient folder";
      return;
    }
    const top = files[0].webkitRelativePath.split("/")[0] || "folder";
    const c3ds = files.filter((f) => f.name.toLowerCase().endsWith(".c3d"));
    label.textContent = `${top} (${files.length} files, ${c3ds.length} C3D)`;
    if (!$("subject_id").dataset.touched) {
      $("subject_id").value = top;
    }
  });
  $("subject_id").addEventListener("input", () => {
    $("subject_id").dataset.touched = "1";
  });
}

async function loadMarkersFromFolder(apiBase) {
  const files = [...$("folder-input").files];
  const cal = pickCalC3d(files);
  if (!cal) throw new Error("Choose a patient folder with a .c3d first.");
  $("map-status").textContent = `Reading markers from ${cal.name}…`;
  const body = new FormData();
  body.append("file", cal, cal.name);
  const res = await fetch(`${apiBase}/api/inspect_markers`, { method: "POST", body });
  if (!res.ok) {
    const text = await res.text();
    let msg = text;
    try {
      msg = JSON.parse(text).error || text;
    } catch (_) { /* keep */ }
    throw new Error(msg);
  }
  const data = await res.json();
  const all = data.source_markers || [];
  sourceMarkers = all.filter(isLikelySurface);
  renderMapTable();
  $("map-status").textContent =
    `${sourceMarkers.length} surface labels from ${data.file}` +
    (all.length > sourceMarkers.length
      ? ` (${all.length - sourceMarkers.length} virtual/angle labels hidden).`
      : ".") +
    " Adjust mappings, then run.";
}

async function runLocal(appCfg, form) {
  const files = [...$("folder-input").files];
  if (!files.length) throw new Error("Choose a patient folder first.");
  $("status").textContent = `Uploading ${files.length} files and running pipeline…`;
  const body = new FormData();
  body.append("config_yaml", buildYaml(appCfg.trialTemplate, form));
  body.append("marker_map_yaml", collectMarkerMapYaml());
  for (const file of files) {
    const rel = file.webkitRelativePath || file.name;
    body.append("files", file, rel);
  }
  const res = await fetch(`${appCfg.api_base}/api/process`, { method: "POST", body });
  if (!res.ok) {
    const text = await res.text();
    let msg = text || `Server error ${res.status}`;
    try {
      const j = JSON.parse(text);
      if (j.error) msg = j.error;
    } catch (_) { /* keep text */ }
    throw new Error(msg);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const run = res.headers.get("X-Gait-Run") || "run";
  $("download").hidden = false;
  $("download").innerHTML = `<a href="${url}" download="${run}.zip">Download ${run}.zip</a>`;
  $("status").textContent = `Done (${run}). outputs/${run} · logs/${run}`;
}

async function onSubmit(e, appCfg) {
  e.preventDefault();
  const btn = $("run-btn");
  btn.disabled = true;
  $("download").hidden = true;
  try {
    await runLocal(appCfg, e.target);
  } catch (err) {
    $("status").textContent = String(err.message || err);
  } finally {
    btn.disabled = false;
  }
}

async function boot() {
  try {
    wireFolder();
    const appCfg = await loadAppConfig();
    appCfg.trialTemplate = await loadTrialTemplate();
    setup = await loadMarkerSetup(appCfg.api_base);
    renderMapTable();
    renderAverages();
    $("load-markers-btn").addEventListener("click", async () => {
      try {
        await loadMarkersFromFolder(appCfg.api_base);
      } catch (err) {
        $("map-status").textContent = String(err.message || err);
      }
    });
    const health = await fetch(`${appCfg.api_base}/api/health`);
    $("status").textContent = health.ok
      ? `Ready (local server ${appCfg.api_base}).`
      : "Local server not reachable — start scripts/local_server.py";
    $("job-form").addEventListener("submit", (e) => onSubmit(e, appCfg));
  } catch (err) {
    $("status").textContent =
      `Start the local server first: PYTHONPATH=src python scripts/local_server.py (${err.message || err})`;
    wireFolder();
  }
}

boot();
