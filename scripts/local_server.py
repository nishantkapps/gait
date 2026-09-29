"""Local HTTP server: serve web UI + process an uploaded subject folder."""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from gait.config import load_yaml
from gait.run_subject_dir import run_subject_dir

ROOT = Path(__file__).resolve().parents[1]


def create_app(cfg: dict) -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app, origins=cfg["cors_origins"])
    web = ROOT / cfg["web_dir"]
    jobs = ROOT / cfg["jobs_dir"]
    jobs.mkdir(parents=True, exist_ok=True)
    _routes(app, web, jobs)
    return app


def _routes(app: Flask, web: Path, jobs: Path) -> None:
    @app.get("/")
    def index():
        return send_from_directory(web, "index.html")

    @app.get("/<path:name>")
    def static_file(name: str):
        return send_from_directory(web, name)

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.post("/api/process")
    def process():
        return _handle_process(request, jobs)


def _handle_process(req, jobs: Path):
    uploads = req.files.getlist("files")
    if not uploads:
        return jsonify({"error": "missing folder upload (files)"}), 400
    if "config_yaml" not in req.form:
        return jsonify({"error": "missing config_yaml"}), 400
    job_dir = jobs / f"job-{int(time.time() * 1000)}"
    src = job_dir / "input"
    src.mkdir(parents=True, exist_ok=True)
    try:
        _save_folder_upload(uploads, src)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    cfg_path = job_dir / "trial.yaml"
    cfg_path.write_text(req.form["config_yaml"], encoding="utf-8")
    out = job_dir / "out"
    try:
        run_subject_dir(str(cfg_path), str(src), str(out))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return send_file(_zip_dir(out), as_attachment=True, download_name="gait-outputs.zip")


def _save_folder_upload(uploads, dest: Path) -> None:
    saved = 0
    for upload in uploads:
        if not upload.filename:
            continue
        rel = Path(upload.filename)
        # Browser sends "FolderName/file.c3d" — strip the top folder name.
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
