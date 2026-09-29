"""OpenSim Scale, IK, and ID — setups stay in config; all outputs go to out_dir."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def _copy_setup(setup_xml: str, out_dir: Path) -> str:
    """Run tools from a setup copy inside out_dir so relative writes never hit config/."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / Path(setup_xml).name
    shutil.copy2(setup_xml, dest)
    return str(dest.resolve())


def _rel_to_setup(setup_xml: str, path: str) -> str:
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

    out_model = Path(output_model).resolve()
    out_dir = out_model.parent
    setup = _copy_setup(setup_xml, out_dir)
    tool = osim.ScaleTool(setup)
    tool.setSubjectMass(float(mass_kg))
    gmm = tool.getGenericModelMaker()
    gmm.setModelFileName(_rel_to_setup(setup, model_path))
    if marker_set:
        gmm.setMarkerSetFileName(_rel_to_setup(setup, marker_set))
    trc = _rel_to_setup(setup, marker_trc)
    out = _rel_to_setup(setup, str(out_model))
    tool.getModelScaler().setMarkerFileName(trc)
    tool.getModelScaler().setOutputModelFileName(out)
    placer = tool.getMarkerPlacer()
    placer.setMarkerFileName(trc)
    placer.setOutputModelFileName(out)
    placer.setOutputMotionFileName(_rel_to_setup(setup, str(out_dir / "scale_output.mot")))
    placer.setOutputMarkerFileName(
        _rel_to_setup(setup, str(out_dir / "scaled_markerset.xml"))
    )
    if not tool.run():
        raise RuntimeError(f"Scale failed: {setup_xml}")


def run_ik(
    scaled_model: str,
    setup_xml: str,
    output_mot: str,
    marker_trc: str,
) -> None:
    import opensim as osim

    out_mot = Path(output_mot).resolve()
    out_dir = out_mot.parent
    setup = _copy_setup(setup_xml, out_dir)
    model = osim.Model(str(Path(scaled_model).resolve()))
    tool = osim.InverseKinematicsTool(setup)
    tool.setModel(model)
    tool.setResultsDir(".")
    tool.setMarkerDataFileName(_rel_to_setup(setup, marker_trc))
    tool.setOutputMotionFileName(_rel_to_setup(setup, str(out_mot)))
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

    out_sto = Path(output_sto).resolve()
    out_dir = out_sto.parent
    setup = _copy_setup(setup_xml, out_dir)
    model = osim.Model(str(Path(scaled_model).resolve()))
    model.initSystem()
    tool = osim.InverseDynamicsTool(setup)
    tool.setModel(model)
    tool.setResultsDir(".")
    tool.setCoordinatesFileName(_rel_to_setup(setup, coordinates_file))
    tool.setExternalLoadsFileName(_rel_to_setup(setup, external_loads_file))
    tool.setOutputGenForceFileName(_rel_to_setup(setup, str(out_sto)))
    if not tool.run():
        raise RuntimeError(f"ID failed: {setup_xml}")
