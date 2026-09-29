const $ = (id) => document.getElementById(id);

async function loadAppConfig() {
  const res = await fetch("app.config.json");
  return res.json();
}

async function loadTrialTemplate() {
  const res = await fetch("trial.template.yaml");
  return res.text();
}

function adapterType(fileName) {
  const ext = fileName.split(".").pop().toLowerCase();
  if (ext === "c3d") return "c3d";
  return "csv";
}

function buildYaml(template, form, fileName) {
  const height = Number(form.height_m.value);
  return template
    .replaceAll("__ADAPTER_TYPE__", adapterType(fileName))
    .replaceAll("__SUBJECT_ID__", form.subject_id.value.trim())
    .replaceAll("__MASS_KG__", String(Number(form.mass_kg.value)))
    .replaceAll("__HEIGHT_M__", Number.isFinite(height) ? String(height) : "null")
    .replaceAll("__TRIAL_ID__", form.trial_id.value.trim() || "walk01");
}

function wireDrop() {
  const zone = $("drop-zone");
  const input = $("source-file");
  const label = $("drop-label");
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("drag"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag");
    if (e.dataTransfer.files[0]) {
      input.files = e.dataTransfer.files;
      label.textContent = e.dataTransfer.files[0].name;
    }
  });
  input.addEventListener("change", () => {
    if (input.files[0]) label.textContent = input.files[0].name;
  });
}

async function runLocal(appCfg, file, form) {
  $("status").textContent = "Running local pipeline…";
  const body = new FormData();
  body.append("source", file, file.name);
  body.append("config_yaml", buildYaml(appCfg.trialTemplate, form, file.name));
  const res = await fetch(`${appCfg.api_base}/api/process`, { method: "POST", body });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Server error ${res.status}`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  $("download").hidden = false;
  $("download").innerHTML = `<a href="${url}" download="gait-outputs.zip">Download gait-outputs.zip</a>`;
  $("status").textContent = "Done.";
}

async function onSubmit(e, appCfg) {
  e.preventDefault();
  const file = $("source-file").files[0];
  if (!file) {
    $("status").textContent = "Choose a source file first.";
    return;
  }
  const btn = $("run-btn");
  btn.disabled = true;
  $("download").hidden = true;
  try {
    await runLocal(appCfg, file, e.target);
  } catch (err) {
    $("status").textContent = String(err.message || err);
  } finally {
    btn.disabled = false;
  }
}

async function boot() {
  try {
    wireDrop();
    const appCfg = await loadAppConfig();
    appCfg.trialTemplate = await loadTrialTemplate();
    const health = await fetch(`${appCfg.api_base}/api/health`);
    $("status").textContent = health.ok
      ? `Ready (local server ${appCfg.api_base}).`
      : "Local server not reachable — start scripts/local_server.py";
    $("job-form").addEventListener("submit", (e) => onSubmit(e, appCfg));
  } catch (err) {
    $("status").textContent =
      `Start the local server first: PYTHONPATH=src python scripts/local_server.py (${err.message || err})`;
    wireDrop();
  }
}

boot();
