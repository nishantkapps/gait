# OpenSim setup files only (no run outputs)

Keep here:

- `scale_setup.xml`, `ik_setup.xml`, `id_setup.xml`
- `markerset_walk_preScale.xml`, `scaleSet_applied_walk.xml`

The pipeline **copies** these into `data/outputs/run_XXX/results/...` for each run.
All `.mot` / `.sto` / `.osim` / marker outputs are written under `data/outputs/`, never here.
