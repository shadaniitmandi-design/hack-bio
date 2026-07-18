from fastapi import FastAPI, APIRouter, HTTPException
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

from admet_predictor import get_predictor


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
        latency_ms=latency_ms,
        source="model",
    )


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