# gait

Generic **markers + forces → OpenSim Scale / IK / ID** pipeline.

## Setup

```bash
# Python deps (C3D + config)
pip install -r requirements.txt

# OpenSim bindings (conda-forge)
conda install -c opensim-org opensim

# Place generic Rajagopal model at the path in your YAML (default models/Rajagopal2016.osim)
# Place Scale / IK / ID setup XML under config/opensim/ (see config/opensim/README.md)
```

## Configure

Copy `config/pipeline.example.yaml` and edit subject mass, force-plate analog channels, marker map, and OpenSim setup paths.

## Run

```bash
export PYTHONPATH=src
python scripts/run_trial.py --config config/pipeline.example.yaml --source data/raw/trial.c3d
```

Outputs land in `data/processed/<subject_id>/` (`.trc`, GRF `.mot`, ExternalLoads `.xml`, scaled `.osim`, IK `.mot`, ID `.sto`). Load them in OpenSim or OpenSim Creator.

## Web app (GitHub Pages)

Static UI in `web/`. Pages cannot run OpenSim; the UI uploads to `inbox/` and runs `.github/workflows/process-trial.yml`, then you download Action artifacts (`.trc` / GRF when configured).

1. Repo **Settings → Pages → Source: GitHub Actions**
2. Push `main` (deploys `web/` via `deploy-pages.yml`)
3. Open `https://<user>.github.io/gait/`
4. Use a fine-grained PAT with **Contents** + **Actions** read/write on this repo
5. Set `default_owner` in `web/app.config.json` if you want it prefilled

Local preview:

```bash
cd web && python -m http.server 8080
```

Put a `.c3d` under `data/raw/`, copy `config/pipeline.example.yaml` → `config/my_trial.yaml`, set `subject.mass_kg`, then:

```bash
export PYTHONPATH=src:.

# 1) Inspect marker + analog labels (fill force_plates / marker_map from this)
python tests/test_inspect_c3d.py --source data/raw/your_trial.c3d

# 2) Config load
python tests/test_config.py --config config/my_trial.yaml

# 3) C3D → TrialRecord
python tests/test_c3d_adapter.py --config config/my_trial.yaml --source data/raw/your_trial.c3d

# 4) Marker rename map
python tests/test_mapping.py --config config/my_trial.yaml --source data/raw/your_trial.c3d

# 5) Write .trc
python tests/test_write_trc.py --config config/my_trial.yaml --source data/raw/your_trial.c3d

# 6) Write GRF .mot + ExternalLoads (needs force_plates filled)
python tests/test_write_grf.py --config config/my_trial.yaml --source data/raw/your_trial.c3d

# 7–9) OpenSim (needs model + setup XMLs)
python tests/test_scale.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_ik.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_id.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
```
