const $ = (id) => document.getElementById(id);

async function loadAppConfig() {
  const res = await fetch("app.config.json");
  return res.json();
}

async function loadTrialTemplate() {
  const res = await fetch("trial.template.yaml");
  return res.text();
}

function buildYaml(template, form) {
  const height = Number(form.height_m.value);
  return template
    .replaceAll("__SUBJECT_ID__", form.subject_id.value.trim())
    .replaceAll("__MASS_KG__", String(Number(form.mass_kg.value)))
    .replaceAll("__HEIGHT_M__", Number.isFinite(height) ? String(height) : "null");
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

async function runLocal(appCfg, form) {
  const files = [...$("folder-input").files];
  if (!files.length) throw new Error("Choose a patient folder first.");
  $("status").textContent = `Uploading ${files.length} files and running pipeline…`;
  const body = new FormData();
  body.append("config_yaml", buildYaml(appCfg.trialTemplate, form));
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
  $("download").hidden = false;
  $("download").innerHTML = `<a href="${url}" download="gait-outputs.zip">Download gait-outputs.zip</a>`;
  $("status").textContent = "Done.";
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
