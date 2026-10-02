from pathlib import Path
import json
import shutil
import subprocess
import sys
import uuid
from pydantic import BaseModel, Field
from src.search_contract import search
import hashlib
from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parents[1]

UPLOAD_DIR = BASE_DIR / "data" / "processed" / "uploads"

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural-language contract search query")
    top_k: int = Field(default=5, ge=1, le=10, description="Number of results to return")

REPORT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "contract_analysis_report.json"
)

CLAUSE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "detected_clauses.json"
)

RISK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "analysis"
    / "risk_report.json"
)


UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title="AI-Powered Contract Intelligence & Risk Scoring API",
    description=(
        "API for contract clause detection, "
        "risk scoring and explainable contract analysis."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Frontend configuration
# -------------------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "app" / "static")),
    name="static",
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "app" / "templates")
)


# -------------------------------------------------------------------
# Utility
# -------------------------------------------------------------------

def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required report file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_file_metadata(file_path: Path):
    """Return metadata for a saved contract PDF."""

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Uploaded contract not found."
        )

    sha256_hash = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256_hash.update(chunk)

    stats = file_path.stat()

    return {
        "stored_filename": file_path.name,
        "file_size_bytes": stats.st_size,
        "file_size_kb": round(stats.st_size / 1024, 2),
        "sha256": sha256_hash.hexdigest(),
        "last_modified_utc": datetime.fromtimestamp(
            stats.st_mtime,
            tz=timezone.utc
        ).isoformat()
    }

# -------------------------------------------------------------------
# Frontend
# -------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


# -------------------------------------------------------------------
# API
# -------------------------------------------------------------------

@app.get("/api")
def api_root():
    return {
        "project": "AI-Powered Contract Intelligence & Risk Scoring",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload-contract",
            "analyze": "/analyze-contract",
            "report": "/risk-report",
            "clauses": "/detected-clauses",
            "risk_details": "/risk-details",
            "download": "/download-report",
            "docs": "/docs",
            "search": "/search",
            "contract_metadata": "/contract-metadata/{stored_filename}",
        },
    }

@app.post("/search")
async def semantic_search(request: SearchRequest):
    results = search(
        query=request.query,
        top_k=request.top_k
    )

    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "contract-intelligence-api",
    }


@app.post("/upload-contract")
async def upload_contract(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file name provided.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF contract files are currently supported.",
        )

    safe_name = f"{uuid.uuid4().hex}.pdf"

    destination = UPLOAD_DIR / safe_name

    try:
        with destination.open("wb") as output:
            shutil.copyfileobj(
                file.file,
                output,
            )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {exc}",
        )

    return {
        "message": "Contract uploaded successfully.",
        "original_filename": file.filename,
        "stored_filename": safe_name,
        "metadata": get_file_metadata(destination)
    }

@app.get("/contract-metadata/{stored_filename}")
def contract_metadata(stored_filename: str):
    """Retrieve metadata for a previously uploaded contract."""

    # Only allow a filename, not a directory path.
    if (
        not stored_filename
        or Path(stored_filename).name != stored_filename
        or not stored_filename.lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid stored PDF filename."
        )

    file_path = UPLOAD_DIR / stored_filename

    return {
        "metadata": get_file_metadata(file_path)
    }


@app.post("/analyze-contract")
async def analyze_contract(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file name provided.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF contract files are currently supported.",
        )

    safe_name = f"{uuid.uuid4().hex}.pdf"

    destination = UPLOAD_DIR / safe_name

    try:

        # -----------------------------------------------------------
        # Save uploaded PDF
        # -----------------------------------------------------------

        with destination.open("wb") as output:
            shutil.copyfileobj(
                file.file,
                output,
            )

        # -----------------------------------------------------------
        # Contract ingestion
        # -----------------------------------------------------------

        ingestion_result = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "src" / "contract_ingestion.py"),
                str(destination),
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if ingestion_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "stage": "contract_ingestion",
                    "error": ingestion_result.stderr,
                    "output": ingestion_result.stdout,
                },
            )

        # -----------------------------------------------------------
        # Clause detection
        # -----------------------------------------------------------

        clause_result = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "src" / "clause_detector.py"),
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if clause_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "stage": "clause_detection",
                    "error": clause_result.stderr,
                    "output": clause_result.stdout,
                },
            )

        # -----------------------------------------------------------
        # Risk scoring
        # -----------------------------------------------------------

        risk_result = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "src" / "risk_scoring.py"),
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if risk_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "stage": "risk_scoring",
                    "error": risk_result.stderr,
                    "output": risk_result.stdout,
                },
            )

        # -----------------------------------------------------------
        # Final combined report
        # -----------------------------------------------------------

        analysis_result = subprocess.run(
            [
                sys.executable,
                str(BASE_DIR / "src" / "analyze_contract.py"),
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
        )

        if analysis_result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "stage": "final_analysis",
                    "error": analysis_result.stderr,
                    "output": analysis_result.stdout,
                },
            )

        # -----------------------------------------------------------
        # Load final report
        # -----------------------------------------------------------

        report = load_json(REPORT_FILE)

        return {
            "message": "Contract analyzed successfully.",
            "filename": file.filename,
            "report": report,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Contract analysis failed: {exc}",
        )


@app.get("/risk-report")
def risk_report():

    try:
        report = load_json(REPORT_FILE)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return report


@app.get("/detected-clauses")
def detected_clauses():

    try:
        clauses = load_json(CLAUSE_FILE)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return clauses


@app.get("/risk-details")
def risk_details():

    try:
        risk = load_json(RISK_FILE)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return risk


@app.get("/download-report")
def download_report():

    if not REPORT_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Analysis report not found.",
        )

    return FileResponse(
        path=REPORT_FILE,
        filename="contract_analysis_report.json",
        media_type="application/json",
    )    