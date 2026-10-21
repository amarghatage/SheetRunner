import shutil
import uuid
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .models import RunConfig
from .runner import execute_run
from .workbooks import validate_workbooks

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="SheetRunner API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS), name="artifacts")
jobs = {}


@app.get("/api/health")
def health(): return {"ok": True}


@app.post("/api/validate")
async def validate(suite: UploadFile = File(...), cases: UploadFile = File(...)):
    temp = UPLOADS / f"validate_{uuid.uuid4().hex}"; temp.mkdir(parents=True)
    try:
        sp, cp = temp / Path(suite.filename).name, temp / Path(cases.filename).name
        sp.write_bytes(await suite.read()); cp.write_bytes(await cases.read())
        return validate_workbooks(sp, cp)
    finally: shutil.rmtree(temp, ignore_errors=True)


@app.post("/api/runs")
async def start_run(suite: UploadFile = File(...), cases: UploadFile = File(...), target_url: str = Form(...), browser: str = Form("chrome"), timeout_seconds: int = Form(10)):
    parsed_url = urlparse(target_url.strip())
    if parsed_url.scheme not in ("http", "https") or not parsed_url.hostname:
        raise HTTPException(422, "Enter a complete target URL, such as https://example.com")
    run_id = uuid.uuid4().hex[:12]
    directory = UPLOADS / run_id; directory.mkdir(parents=True)
    suite_path, cases_path = directory / Path(suite.filename).name, directory / Path(cases.filename).name
    suite_path.write_bytes(await suite.read()); cases_path.write_bytes(await cases.read())
    check = validate_workbooks(suite_path, cases_path)
    if not check["valid"]:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(422, detail=check["issues"])
    config = RunConfig(target_url=target_url, browser=browser, suite_path=str(suite_path), cases_path=str(cases_path), screenshot_dir=str(ROOT / "artifacts" / run_id / "screenshots"), output_dir=str(ROOT / "artifacts" / run_id), timeout_seconds=timeout_seconds)
    jobs[run_id] = {"status": "running", "result": None}
    Thread(target=execute_run, args=(run_id, config, jobs), daemon=True).start()
    return {"run_id": run_id, "status": "running"}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    if run_id not in jobs: raise HTTPException(404, "Run not found")
    return jobs[run_id]
