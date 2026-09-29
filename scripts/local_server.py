"""Local HTTP server: serve web UI + run Workstream A on upload."""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from gait.config import load_yaml
from gait.run_job import run_job

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
    upload = req.files.get("source")
    if upload is None or not upload.filename:
        return jsonify({"error": "missing source file"}), 400
    if "config_yaml" not in req.form:
        return jsonify({"error": "missing config_yaml"}), 400
    job_dir = jobs / f"job-{int(time.time() * 1000)}"
    job_dir.mkdir(parents=True, exist_ok=True)
    src = job_dir / Path(upload.filename).name
    upload.save(src)
    cfg_path = job_dir / "trial.yaml"
    cfg_path.write_text(req.form["config_yaml"], encoding="utf-8")
    out = job_dir / "out"
    try:
        run_job(str(cfg_path), str(src), str(out))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return send_file(_zip_dir(out), as_attachment=True, download_name="gait-outputs.zip")


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
