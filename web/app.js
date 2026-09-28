const $ = (id) => document.getElementById(id);

async function loadAppConfig() {
  const res = await fetch("app.config.json");
  return res.json();
}

function buildYaml(form) {
  const id = form.subject_id.value.trim();
  return [
    "adapter:",
    "  type: c3d",
    "paths:",
    "  processed_dir: data/processed",
    "  marker_map: config/marker_maps/example.yaml",
    "subject:",
    `  subject_id: ${id}`,
    `  mass_kg: ${Number(form.mass_kg.value)}`,
    `  height_m: ${Number(form.height_m.value) || null}`,
    "  hemiplegic_side: null",
    `  trial_id: ${form.trial_id.value.trim() || "walk01"}`,
    "units:",
    "  marker_input: mm",
    "  trc_output: m",
    "lab_axes:",
    "  from_lab_to_opensim:",
    "    - [1.0, 0.0, 0.0]",
    "    - [0.0, 1.0, 0.0]",
    "    - [0.0, 0.0, 1.0]",
    "force_plates: []",
    "opensim:",
    "  enabled: false",
    "  ground_body: ground",
    "  generic_model: models/Rajagopal2016.osim",
    "  scale_setup: config/opensim/scale_setup.xml",
    "  ik_setup: config/opensim/ik_setup.xml",
    "  id_setup: config/opensim/id_setup.xml",
    "  outputs:",
    "    trc: markers.trc",
    "    grf_mot: grf.mot",
    "    external_loads: external_loads.xml",
    "    scaled_model: scaled.osim",
    "    ik_mot: ik.mot",
    "    id_sto: id.sto",
    "",
  ].join("\n");
}

function toBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

async function putFile(owner, repo, token, path, contentB64, message) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
  const res = await fetch(url, {
    method: "PUT",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, content: contentB64 }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function dispatchWorkflow(owner, repo, token, workflow, jobId) {
  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ ref: "main", inputs: { job_id: jobId } }),
  });
  if (!res.ok) throw new Error(await res.text());
}

async function findRun(owner, repo, token, jobId) {
  const url = `https://api.github.com/repos/${owner}/${repo}/actions/workflows/process-trial.yml/runs?event=workflow_dispatch&per_page=10`;
  const res = await fetch(url, {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return (data.workflow_runs || []).find((r) => r.name.includes(jobId) || r.display_title?.includes(jobId));
}

async function waitForArtifact(owner, repo, token, runId, appCfg) {
  for (let i = 0; i < appCfg.max_polls; i += 1) {
    const runRes = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/actions/runs/${runId}`,
      { headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${token}` } },
    );
    const run = await runRes.json();
    $("status").textContent = `Job ${run.status}${run.conclusion ? ` (${run.conclusion})` : ""}…`;
    if (run.status === "completed") {
      if (run.conclusion !== "success") throw new Error(`Workflow failed: ${run.conclusion}`);
      return listArtifacts(owner, repo, token, runId);
    }
    await new Promise((r) => setTimeout(r, appCfg.poll_ms));
  }
  throw new Error("Timed out waiting for Actions");
}

async function listArtifacts(owner, repo, token, runId) {
  const res = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/actions/runs/${runId}/artifacts`,
    { headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${token}` } },
  );
  const data = await res.json();
  const art = (data.artifacts || [])[0];
  if (!art) throw new Error("No artifact produced");
  return art;
}

function wireDrop() {
  const zone = $("drop-zone");
  const input = $("c3d-file");
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

async function uploadJob(owner, repo, token, prefix, jobId, file, form) {
  $("status").textContent = "Uploading C3D…";
  const c3dBuf = await file.arrayBuffer();
  await putFile(owner, repo, token, `${prefix}/trial.c3d`, toBase64(c3dBuf), `inbox ${jobId} c3d`);
  $("status").textContent = "Uploading config…";
  const yaml = buildYaml(form);
  const yamlB64 = btoa(unescape(encodeURIComponent(yaml)));
  await putFile(owner, repo, token, `${prefix}/trial.yaml`, yamlB64, `inbox ${jobId} yaml`);
}

async function startAndWait(owner, repo, token, appCfg, jobId) {
  $("status").textContent = "Starting Actions workflow…";
  await dispatchWorkflow(owner, repo, token, appCfg.workflow_file, jobId);
  await new Promise((r) => setTimeout(r, 3000));
  let run = await findRun(owner, repo, token, jobId);
  for (let i = 0; !run && i < 10; i += 1) {
    await new Promise((r) => setTimeout(r, 2000));
    run = await findRun(owner, repo, token, jobId);
  }
  if (!run) throw new Error("Could not find workflow run");
  const art = await waitForArtifact(owner, repo, token, run.id, appCfg);
  return { run, art };
}

async function onSubmit(e, appCfg) {
  e.preventDefault();
  const btn = $("run-btn");
  const file = $("c3d-file").files[0];
  if (!file) return;
  btn.disabled = true;
  $("download").hidden = true;
  try {
    const owner = $("gh_owner").value.trim();
    const repo = $("gh_repo").value.trim();
    const token = $("gh_token").value.trim();
    const jobId = `job-${Date.now()}`;
    const prefix = `${appCfg.inbox_prefix}/${jobId}`;
    await uploadJob(owner, repo, token, prefix, jobId, file, e.target);
    const { run, art } = await startAndWait(owner, repo, token, appCfg, jobId);
    $("status").textContent = "Done.";
    $("download").hidden = false;
    $("download").innerHTML = `Download from Actions (login): <a href="${run.html_url}" target="_blank" rel="noopener">open run</a> · <strong>${art.name}</strong>`;
  } catch (err) {
    $("status").textContent = String(err.message || err);
  } finally {
    btn.disabled = false;
  }
}

wireDrop();
const appCfg = await loadAppConfig();
if (appCfg.default_owner) $("gh_owner").value = appCfg.default_owner;
if (appCfg.default_repo) $("gh_repo").value = appCfg.default_repo;
$("job-form").addEventListener("submit", (e) => onSubmit(e, appCfg));
