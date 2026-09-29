# gait

Generic **markers + forces → OpenSim Scale / IK / ID** pipeline.

## Setup

```bash
pip install -r requirements.txt

# OpenSim bindings (conda-forge), only if you run Scale/IK/ID
conda install -c opensim-org opensim

# Place Rajagopal model at the path in your YAML (default models/Rajagopal2016.osim)
# Place Scale / IK / ID setup XML under config/opensim/ (see config/opensim/README.md)
```

## Local web app + server

```bash
export PYTHONPATH=src
python scripts/local_server.py
```

Open **http://127.0.0.1:8000/** — drop a file, click **Run pipeline**, download `gait-outputs.zip`.

- Server: `config/server.yaml`
- UI API base: `web/app.config.json` (`api_base`)

## CLI

```bash
export PYTHONPATH=src
python scripts/run_trial.py --config config/pipeline.example.yaml --source data/raw/trial.c3d
```

Copy `config/pipeline.example.yaml` and edit subject mass, force-plate channels, marker map, and OpenSim paths.

Outputs: `data/processed/<subject_id>/` (`.trc`, GRF `.mot`, ExternalLoads `.xml`, and Scale/IK/ID when enabled).

## Piece-wise tests

```bash
export PYTHONPATH=src:.

python tests/test_inspect_c3d.py --source data/raw/your_trial.c3d
python tests/test_config.py --config config/my_trial.yaml
python tests/test_c3d_adapter.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_mapping.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_write_trc.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_write_grf.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_scale.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_ik.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
python tests/test_id.py --config config/my_trial.yaml --source data/raw/your_trial.c3d
```
