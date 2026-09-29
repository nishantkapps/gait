# OpenSim Scale / IK / ID setup files (required for full A outputs)

Place these files here (paths match `web/trial.template.yaml` / pipeline YAML):

- `scale_setup.xml` — ScaleTool (static markers TRC + mass)
- `ik_setup.xml` — InverseKinematicsTool (dynamic markers TRC)
- `id_setup.xml` — InverseDynamicsTool (IK MOT + ExternalLoads)

Also place the generic model at:

- `models/Rajagopal2016.osim`

Without the model + these XMLs, the local server can still write `markers.trc`
(and GRF files if force columns are configured), but not `scaled.osim` / `ik.mot` / `id.sto`.

Export setups from the OpenSim GUI, and point them at the trial outputs under
`data/jobs/.../out/` or `data/processed/<subject_id>/`.
