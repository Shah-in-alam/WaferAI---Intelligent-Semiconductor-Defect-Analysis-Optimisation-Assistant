"""FastAPI backend for the TypeScript frontend.

Wraps the existing src/ pipeline (classifier, preprocessor, analyzer, PDF
report builder) behind a REST API + an SSE endpoint for streaming chat.
"""
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src import (
    WaferAnalyzer,
    WaferClassifier,
    WaferPreprocessor,
    build_pdf_report,
    overlay_gradcam,
)
from src.utils import get_logger, project_root

load_dotenv()
logger = get_logger(__name__)

ROOT = project_root()
SAMPLES_DIR = ROOT / "data" / "sample_wafers"
WEB_DIST = ROOT / "web" / "dist"

preprocessor = WaferPreprocessor()
classifier = WaferClassifier(model_path=os.getenv("MODEL_PATH"))
analyzer = WaferAnalyzer()

app = FastAPI(title="WaferAI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    using_stub_classifier: bool
    claude_configured: bool
    claude_model: Optional[str] = None
    sample_count: int


class AnalysisModel(BaseModel):
    defect_type: str
    severity: str
    root_causes: list[str]
    immediate_actions: list[str]
    process_improvements: list[str]
    quality_impact: str
    estimated_yield_loss: str


class MetadataModel(BaseModel):
    width: int
    height: int
    defect_density: float
    location: str


class AnalyzeResponse(BaseModel):
    defect_type: str
    confidence: float
    probabilities: dict[str, float]
    metadata: MetadataModel
    analysis: AnalysisModel
    overlay_png_b64: str
    pdf_b64: str


class ChatRequest(BaseModel):
    message: str


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        using_stub_classifier=classifier.using_stub,
        claude_configured=analyzer.client is not None,
        claude_model=analyzer.model if analyzer.client else None,
        sample_count=len(list(SAMPLES_DIR.glob("*.png"))) if SAMPLES_DIR.exists() else 0,
    )


@app.get("/api/samples")
def list_samples() -> list[str]:
    if not SAMPLES_DIR.exists():
        return []
    return sorted(p.name for p in SAMPLES_DIR.glob("*.png"))


@app.get("/api/samples/{name}")
def get_sample(name: str):
    safe = Path(name).name
    path = SAMPLES_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="sample not found")
    return FileResponse(path, media_type="image/png")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(image: UploadFile = File(...)) -> AnalyzeResponse:
    contents = await image.read()
    try:
        pil = Image.open(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"cannot decode image: {exc}")

    if not preprocessor.validate_image(pil):
        raise HTTPException(status_code=400, detail="invalid image")

    tensor = preprocessor.preprocess_for_model(pil)
    metadata = preprocessor.extract_metadata(pil)
    defect_type, confidence = classifier.predict(tensor)
    probs = classifier.predict_proba(tensor)
    heat = classifier.generate_gradcam(tensor)
    overlay = overlay_gradcam(pil, heat)

    defect_info = {
        "defect_pattern": defect_type,
        "model_confidence": confidence,
        **metadata,
    }
    analysis = analyzer.analyze(defect_info)

    overlay_buf = io.BytesIO()
    overlay.save(overlay_buf, format="PNG")
    overlay_b64 = base64.b64encode(overlay_buf.getvalue()).decode("ascii")

    pdf_buf = io.BytesIO()
    build_pdf_report(pdf_buf, pil, overlay, defect_info, analysis)
    pdf_b64 = base64.b64encode(pdf_buf.getvalue()).decode("ascii")

    return AnalyzeResponse(
        defect_type=defect_type,
        confidence=confidence,
        probabilities=probs,
        metadata=MetadataModel(**metadata),
        analysis=AnalysisModel(**analysis.model_dump()),
        overlay_png_b64=overlay_b64,
        pdf_b64=pdf_b64,
    )


@app.post("/api/chat")
async def chat(req: ChatRequest):
    async def event_stream():
        try:
            for token in analyzer.stream_chat(req.message):
                yield {"event": "token", "data": json.dumps(token)}
        except Exception as exc:
            logger.exception("stream_chat failed")
            yield {"event": "error", "data": json.dumps(str(exc))}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_stream())


# Production: serve the built React bundle from /. Must be mounted LAST,
# after every /api/* route is registered.
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
