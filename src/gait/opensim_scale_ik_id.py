"""OpenSim Scale, IK, and ID using setup paths from config."""

from __future__ import annotations

import os
from pathlib import Path


def _rel_to_setup(setup_xml: str, path: str) -> str:
    """OpenSim joins file names onto the setup XML directory — never pass abs paths."""
    setup_dir = Path(setup_xml).resolve().parent
    return os.path.relpath(Path(path).resolve(), setup_dir)


def run_scale(
    model_path: str,
    setup_xml: str,
    output_model: str,
    marker_trc: str,
    mass_kg: float,
    marker_set: str | None = None,
) -> None:
    import opensim as osim

    setup = str(Path(setup_xml).resolve())
    Path(output_model).parent.mkdir(parents=True, exist_ok=True)
    tool = osim.ScaleTool(setup)
    tool.setSubjectMass(float(mass_kg))
    gmm = tool.getGenericModelMaker()
    gmm.setModelFileName(_rel_to_setup(setup, model_path))
    if marker_set:
        gmm.setMarkerSetFileName(_rel_to_setup(setup, marker_set))
    trc = _rel_to_setup(setup, marker_trc)
    out = _rel_to_setup(setup, output_model)
    tool.getModelScaler().setMarkerFileName(trc)
    tool.getModelScaler().setOutputModelFileName(out)
    tool.getMarkerPlacer().setMarkerFileName(trc)
    tool.getMarkerPlacer().setOutputModelFileName(out)
    if not tool.run():
        raise RuntimeError(f"Scale failed: {setup_xml}")


def run_ik(
    scaled_model: str,
    setup_xml: str,
    output_mot: str,
    marker_trc: str,
) -> None:
    import opensim as osim

    setup = str(Path(setup_xml).resolve())
    Path(output_mot).parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(str(Path(scaled_model).resolve()))
    tool = osim.InverseKinematicsTool(setup)
    tool.setModel(model)
    tool.setMarkerDataFileName(_rel_to_setup(setup, marker_trc))
    tool.setOutputMotionFileName(_rel_to_setup(setup, output_mot))
    if not tool.run():
        raise RuntimeError(f"IK failed: {setup_xml}")


def run_id(
    scaled_model: str,
    setup_xml: str,
    output_sto: str,
    coordinates_file: str,
    external_loads_file: str,
) -> None:
    import opensim as osim

    setup = str(Path(setup_xml).resolve())
    Path(output_sto).parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(str(Path(scaled_model).resolve()))
    model.initSystem()
    tool = osim.InverseDynamicsTool(setup)
    tool.setModel(model)
    tool.setCoordinatesFileName(_rel_to_setup(setup, coordinates_file))
    tool.setExternalLoadsFileName(_rel_to_setup(setup, external_loads_file))
    tool.setOutputGenForceFileName(_rel_to_setup(setup, output_sto))
    if not tool.run():
        raise RuntimeError(f"ID failed: {setup_xml}")
