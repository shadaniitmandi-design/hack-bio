from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import time
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

from admet_predictor import get_predictor, parse_smiles_csv, results_to_csv


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}


# ========== ADMET Prediction ==========

class PredictRequest(BaseModel):
    smiles: str


class PredictResponse(BaseModel):
    smiles: str
    results: Dict[str, Any]
    descriptors: Dict[str, Any]
    scaffold: Dict[str, Any]
    latency_ms: int
    source: str  # "model" or "mock"


@api_router.get("/health")
async def health():
    predictor = get_predictor()
    return {
        "status": "ok",
        "model_loaded": predictor.available,
        "endpoints": list(predictor.models.keys()),
        "errors": predictor.load_errors,
    }


@api_router.post("/predict", response_model=PredictResponse)
async def predict_admet(req: PredictRequest):
    smiles = (req.smiles or "").strip()
    if not smiles:
        raise HTTPException(status_code=400, detail="SMILES string is required")

    predictor = get_predictor()
    if not predictor.available:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.perf_counter()
    try:
        descriptors = predictor.descriptors(smiles)
        scaffold = predictor.scaffold_info(smiles)
        results = predictor.predict(smiles)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

    latency_ms = int((time.perf_counter() - start) * 1000)

    # Persist to history (fire-and-forget style but await for reliability)
    try:
        doc = {
            "id": str(uuid.uuid4()),
            "smiles": smiles,
            "results": results,
            "descriptors": descriptors,
            "scaffold": scaffold,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await db.admet_history.insert_one(doc)
    except Exception:
        logger.exception("Could not persist history")

    return PredictResponse(
        smiles=smiles,
        results=results,
        descriptors=descriptors,
        scaffold=scaffold,
        latency_ms=latency_ms,
        source="model",
    )


# ---------- Scaffold-only lookup ----------

class ScaffoldRequest(BaseModel):
    smiles: str


@api_router.post("/scaffold")
async def scaffold_endpoint(req: ScaffoldRequest):
    smiles = (req.smiles or "").strip()
    if not smiles:
        raise HTTPException(status_code=400, detail="SMILES string is required")
    predictor = get_predictor()
    try:
        return {
            "smiles": smiles,
            "scaffold": predictor.scaffold_info(smiles),
            "descriptors": predictor.descriptors(smiles),
        }
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))


# ---------- Batch prediction ----------

class BatchPredictRequest(BaseModel):
    items: List[Dict[str, Any]]  # each: {row_idx?, name?, smiles}


class BatchPredictItem(BaseModel):
    row_idx: int
    name: Optional[str] = None
    smiles: str
    results: Optional[Dict[str, Any]] = None
    descriptors: Optional[Dict[str, Any]] = None
    scaffold: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BatchPredictResponse(BaseModel):
    count: int
    ok: int
    failed: int
    latency_ms: int
    items: List[BatchPredictItem]


def _run_batch(items: List[dict]) -> List[dict]:
    predictor = get_predictor()
    out: List[dict] = []
    for i, it in enumerate(items):
        s = (it.get("smiles") or "").strip()
        row_idx = int(it.get("row_idx") or (i + 1))
        name = it.get("name") or ""
        if not s:
            out.append({"row_idx": row_idx, "name": name, "smiles": s, "error": "empty"})
            continue
        try:
            out.append({
                "row_idx": row_idx,
                "name": name,
                "smiles": s,
                "results": predictor.predict(s),
                "descriptors": predictor.descriptors(s),
                "scaffold": predictor.scaffold_info(s),
            })
        except ValueError as ve:
            out.append({"row_idx": row_idx, "name": name, "smiles": s, "error": str(ve)})
        except Exception as exc:
            out.append({"row_idx": row_idx, "name": name, "smiles": s, "error": f"failure: {exc}"})
    return out


@api_router.post("/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(req: BatchPredictRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="items list is empty")
    if len(req.items) > 500:
        raise HTTPException(status_code=413, detail="Max 500 rows per batch")
    predictor = get_predictor()
    if not predictor.available:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.perf_counter()
    items = _run_batch(req.items)
    latency_ms = int((time.perf_counter() - start) * 1000)
    ok = sum(1 for i in items if not i.get("error"))
    failed = len(items) - ok
    return BatchPredictResponse(count=len(items), ok=ok, failed=failed, latency_ms=latency_ms, items=items)


@api_router.post("/predict/batch/upload", response_model=BatchPredictResponse)
async def predict_batch_upload(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 2 MB)")
    items = parse_smiles_csv(content, max_rows=500)
    if not items:
        raise HTTPException(status_code=422, detail="No SMILES found in file. Expected a 'smiles' column or SMILES in first column.")
    predictor = get_predictor()
    if not predictor.available:
        raise HTTPException(status_code=503, detail="Model not loaded")
    start = time.perf_counter()
    ran = _run_batch(items)
    latency_ms = int((time.perf_counter() - start) * 1000)
    ok = sum(1 for i in ran if not i.get("error"))
    failed = len(ran) - ok
    return BatchPredictResponse(count=len(ran), ok=ok, failed=failed, latency_ms=latency_ms, items=ran)


class BatchCsvExportRequest(BaseModel):
    items: List[Dict[str, Any]]


@api_router.post("/predict/batch/export", response_class=PlainTextResponse)
async def predict_batch_export(req: BatchCsvExportRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="items list is empty")
    return PlainTextResponse(content=results_to_csv(req.items), media_type="text/csv")


class HistoryItem(BaseModel):
    id: str
    smiles: str
    latency_ms: int
    timestamp: str


@api_router.get("/history", response_model=List[HistoryItem])
async def history(limit: int = 20):
    docs = await db.admet_history.find({}, {"_id": 0, "results": 0, "descriptors": 0}).sort("timestamp", -1).to_list(limit)
    return docs

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()