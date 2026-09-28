"""OpenSim Scale, IK, and ID using setup paths from config."""

from __future__ import annotations

from pathlib import Path


def run_scale(model_path: str, setup_xml: str, output_model: str) -> None:
    import opensim as osim

    Path(output_model).parent.mkdir(parents=True, exist_ok=True)
    tool = osim.ScaleTool(setup_xml)
    tool.getGenericModelMaker().setModelFileName(model_path)
    tool.getModelScaler().setOutputModelFileName(output_model)
    if not tool.run():
        raise RuntimeError(f"Scale failed: {setup_xml}")


def run_ik(scaled_model: str, setup_xml: str, output_mot: str) -> None:
    import opensim as osim

    Path(output_mot).parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(scaled_model)
    tool = osim.InverseKinematicsTool(setup_xml)
    tool.setModel(model)
    tool.setOutputMotionFileName(output_mot)
    if not tool.run():
        raise RuntimeError(f"IK failed: {setup_xml}")


def run_id(
    scaled_model: str,
    setup_xml: str,
    output_sto: str,
) -> None:
    import opensim as osim

    Path(output_sto).parent.mkdir(parents=True, exist_ok=True)
    model = osim.Model(scaled_model)
    model.initSystem()
    tool = osim.InverseDynamicsTool(setup_xml)
    tool.setModel(model)
    tool.setOutputGenForceFileName(output_sto)
    if not tool.run():
        raise RuntimeError(f"ID failed: {setup_xml}")
