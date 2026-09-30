"""Local HTTP server: serve web UI + process an uploaded subject folder."""

from __future__ import annotations

import io
import re
import traceback
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from gait.config import load_yaml
from gait.marker_map_ui import (
    c3d_marker_labels,
    default_marker_map,
    opensim_marker_names,
)
from gait.run_layout import allocate_run
from gait.run_log import capture_run_log
from gait.run_subject_dir import run_subject_dir

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKER_MAP = ROOT / "config" / "marker_maps" / "pig_rajagopal.yaml"
DEFAULT_MARKERSET = ROOT / "config" / "opensim" / "markerset_walk_preScale.xml"


def create_app(cfg: dict) -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app, origins=cfg["cors_origins"])
    web = ROOT / cfg["web_dir"]
    outputs_root = ROOT / cfg["outputs_dir"]
    logs_root = ROOT / cfg["logs_dir"]
    outputs_root.mkdir(parents=True, exist_ok=True)
    logs_root.mkdir(parents=True, exist_ok=True)
    _routes(app, web, outputs_root, logs_root)
    return app


def _routes(app: Flask, web: Path, outputs_root: Path, logs_root: Path) -> None:
    @app.get("/")
    def index():
        return send_from_directory(web, "index.html")

    @app.get("/<path:name>")
    def static_file(name: str):
        return send_from_directory(web, name)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/api/marker_setup")
    def marker_setup():
        try:
            mm = default_marker_map(DEFAULT_MARKER_MAP)
            return jsonify(
                {
                    "opensim_markers": opensim_marker_names(DEFAULT_MARKERSET),
                    "default_markers": dict(mm.get("markers") or {}),
                    "default_average_markers": dict(mm.get("average_markers") or {}),
                    "map_path": str(DEFAULT_MARKER_MAP.relative_to(ROOT)),
                }
            )
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/inspect_markers")
    def inspect_markers():
        upload = request.files.get("file")
        if not upload or not upload.filename:
            return jsonify({"error": "missing C3D file"}), 400
        tmp = logs_root / "_inspect"
        tmp.mkdir(parents=True, exist_ok=True)
        path = tmp / Path(upload.filename).name
        upload.save(path)
        try:
            labels = c3d_marker_labels(path)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400
        finally:
            path.unlink(missing_ok=True)
        return jsonify({"source_markers": labels, "file": Path(upload.filename).name})

    @app.post("/api/process")
    def process():
        return _handle_process(request, outputs_root, logs_root)


def _handle_process(req, outputs_root: Path, logs_root: Path):
    uploads = req.files.getlist("files")
    if not uploads:
        return jsonify({"error": "missing folder upload (files)"}), 400
    if "config_yaml" not in req.form:
        return jsonify({"error": "missing config_yaml"}), 400
    run_n, out_dir, log_dir = allocate_run(outputs_root, logs_root)
    src = out_dir / "input"
    src.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "pipeline.log"
    try:
        _save_folder_upload(uploads, src)
    except ValueError as exc:
        return jsonify({"error": str(exc), "run": run_n}), 400
    cfg_path = out_dir / "trial.yaml"
    cfg_text = req.form["config_yaml"]
    if req.form.get("marker_map_yaml"):
        mm_path = out_dir / "marker_map.yaml"
        mm_path.write_text(req.form["marker_map_yaml"], encoding="utf-8")
        # Point this run at the UI-edited map (keep rest of template intact).
        if re.search(r"(?m)^(\s*marker_map:\s*).*$", cfg_text):
            cfg_text = re.sub(
                r"(?m)^(\s*marker_map:\s*).*$",
                rf"\1{mm_path.as_posix()}",
                cfg_text,
            )
        else:
            cfg_text += f"\npaths:\n  marker_map: {mm_path.as_posix()}\n"
    cfg_path.write_text(cfg_text, encoding="utf-8")
    results = out_dir / "results"
    try:
        with capture_run_log(log_path):
            print(f"run_{run_n:03d} output={out_dir} log={log_path}")
            run_subject_dir(str(cfg_path), str(src), str(results))
    except Exception as exc:
        with log_path.open("a", encoding="utf-8") as log_f:
            log_f.write("\n" + traceback.format_exc())
        return jsonify({"error": str(exc), "run": run_n, "log": str(log_path)}), 400
    resp = send_file(
        _zip_dir(results),
        as_attachment=True,
        download_name=f"gait-run_{run_n:03d}.zip",
    )
    resp.headers["X-Gait-Run"] = f"run_{run_n:03d}"
    return resp


def _save_folder_upload(uploads, dest: Path) -> None:
    saved = 0
    for upload in uploads:
        if not upload.filename:
            continue
        rel = Path(upload.filename)
        parts = rel.parts
        if len(parts) > 1:
            rel = Path(*parts[1:])
        target = (dest / rel).resolve()
        if not str(target).startswith(str(dest.resolve())):
            raise ValueError(f"invalid upload path: {upload.filename}")
        target.parent.mkdir(parents=True, exist_ok=True)
        upload.save(target)
        saved += 1
    if saved == 0:
        raise ValueError("folder upload contained no files")


def _zip_dir(out: Path) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in out.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(out).as_posix())
    buf.seek(0)
    return buf


def main() -> None:
    cfg = load_yaml(ROOT / "config" / "server.yaml")
    app = create_app(cfg)
    app.run(host=cfg["host"], port=int(cfg["port"]), debug=False)


if __name__ == "__main__":
    main()
