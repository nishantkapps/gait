"""OpenSim Scale, IK, and ID using setup paths from config."""

from __future__ import annotations

from pathlib import Path


def run_scale(
    model_path: str,
    setup_xml: str,
    output_model: str,
    marker_trc: str,
    mass_kg: float,
    marker_set: str | None = None,
) -> None:
    import opensim as osim

    model = str(Path(model_path).resolve())
    trc = str(Path(marker_trc).resolve())
    out = str(Path(output_model).resolve())
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    tool = osim.ScaleTool(setup_xml)
    tool.setSubjectMass(float(mass_kg))
    gmm = tool.getGenericModelMaker()
    gmm.setModelFileName(model)
    if marker_set:
        gmm.setMarkerSetFileName(str(Path(marker_set).resolve()))
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

    Path(output_mot).parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(str(Path(scaled_model).resolve()))
    tool = osim.InverseKinematicsTool(setup_xml)
    tool.setModel(model)
    tool.setMarkerDataFileName(str(Path(marker_trc).resolve()))
    tool.setOutputMotionFileName(str(Path(output_mot).resolve()))
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

    Path(output_sto).parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(str(Path(scaled_model).resolve()))
    model.initSystem()
    tool = osim.InverseDynamicsTool(setup_xml)
    tool.setModel(model)
    tool.setCoordinatesFileName(str(Path(coordinates_file).resolve()))
    tool.setExternalLoadsFileName(str(Path(external_loads_file).resolve()))
    tool.setOutputGenForceFileName(str(Path(output_sto).resolve()))
    if not tool.run():
        raise RuntimeError(f"ID failed: {setup_xml}")
