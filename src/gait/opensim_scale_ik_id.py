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


def _trc_end_time(trc_path: Path) -> float:
    parts = trc_path.read_text(encoding="utf-8").splitlines()[2].split()
    rate, nframes = float(parts[0]), int(float(parts[2]))
    return max((nframes - 1) / rate, 0.1)


def _add_scale_measurements(scaler, measurements: list) -> None:
    import opensim as osim

    for item in measurements:
        meas = osim.Measurement()
        meas.setName(str(item["name"]))
        meas.setApply(True)
        m1, m2 = item["markers"]
        meas.getMarkerPairSet().adoptAndAppend(osim.MarkerPair(str(m1), str(m2)))
        for body in item["bodies"]:
            bs = osim.BodyScale()
            bs.setName(str(body))
            axes = osim.ArrayStr()
            axes.append("X")
            axes.append("Y")
            axes.append("Z")
            bs.setAxisNames(axes)
            meas.getBodyScaleSet().adoptAndAppend(bs)
        scaler.addMeasurement(meas)
    order = osim.ArrayStr()
    order.append("measurements")
    scaler.setScalingOrder(order)


def run_scale(
    model_path: str,
    setup_xml: str,
    output_model: str,
    marker_trc: str,
    mass_kg: float,
    marker_set: str | None = None,
    measurements: list | None = None,
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
    end_t = _trc_end_time(Path(marker_trc))
    trange = osim.ArrayDouble(0, 0)
    trange.set(0, 0.0)
    trange.set(1, end_t)
    scaler = tool.getModelScaler()
    scaler.setMarkerFileName(trc)
    scaler.setOutputModelFileName(out)
    scaler.setTimeRange(trange)
    scaler.setPreserveMassDist(True)
    if measurements:
        _add_scale_measurements(scaler, measurements)
    placer = tool.getMarkerPlacer()
    placer.setMarkerFileName(trc)
    placer.setOutputModelFileName(out)
    placer.setTimeRange(trange)
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
