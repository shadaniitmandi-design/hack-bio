"""ADMET predictor - loads XGBoost models trained on TDC datasets.

Model source: https://github.com/Mannatkathuria/SMILES_TO_ADMET
Featurizer: Morgan fingerprints (radius=2, 2048 bits)
"""

import os
import io
import csv
import math
import logging
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem.rdMolDescriptors import CalcNumRings
from rdkit.DataStructs import ConvertToNumpyArray

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent / "models"

_ENDPOINT_META = {
    "HIA": {
        "label": "Human Intestinal Absorption",
        "category": "Absorption",
        "code": "HIA",
        "task": "classification",
        "positive": "High Absorption",
        "negative": "Low Absorption",
    },
    "BBB": {
        "label": "Blood-Brain Barrier",
        "category": "Distribution",
        "code": "BBB",
        "task": "classification",
        "positive": "BBB Permeable",
        "negative": "BBB Non-Permeable",
    },
    "CYP2D6": {
        "label": "CYP2D6 Inhibition",
        "category": "Metabolism",
        "code": "CYP2D6",
        "task": "classification",
        "positive": "CYP2D6 Inhibitor",
        "negative": "CYP2D6 Non-Inhibitor",
    },
    "Solubility": {
        "label": "Aqueous Solubility",
        "category": "Absorption",
        "code": "SOL",
        "task": "regression",
        "unit": "logS (mol/L)",
    },
    "VDss": {
        "label": "Volume of Distribution",
        "category": "Distribution",
        "code": "VDss",
        "task": "regression",
        "unit": "L/kg",
    },
}

_MODEL_FILES = {
    "HIA": "hia.pkl",
    "BBB": "bbb.pkl",
    "CYP2D6": "cyp2d6.pkl",
    "Solubility": "solubility.pkl",
    "VDss": "vdss.pkl",
}


def _confidence_tier(sigma: float, scale: float) -> str:
    if scale <= 0:
        return "moderate"
    ratio = sigma / scale
    if ratio < 0.12:
        return "high"
    if ratio < 0.3:
        return "moderate"
    return "low"


class AdmetPredictor:
    def __init__(self):
        self.models = {}
        self.available = True
        self.load_errors = {}
        for key, fname in _MODEL_FILES.items():
            fpath = MODEL_DIR / fname
            if not fpath.exists():
                self.load_errors[key] = f"missing file: {fpath}"
                continue
            try:
                self.models[key] = joblib.load(fpath)
                logger.info(f"Loaded model {key} from {fpath}")
            except Exception as exc:  # noqa: BLE001
                self.load_errors[key] = str(exc)
                logger.exception(f"Failed to load model {key}: {exc}")
        if not self.models:
            self.available = False

    # ---------- Featurization ----------
    @staticmethod
    def _mol(smiles: str):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES string")
        return mol

    @staticmethod
    def _fingerprint(smiles: str) -> np.ndarray:
        mol = AdmetPredictor._mol(smiles)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        arr = np.zeros(2048, dtype=np.int8)
        ConvertToNumpyArray(fp, arr)
        return arr.reshape(1, -1)

    # ---------- Descriptors ----------
    @staticmethod
    def descriptors(smiles: str) -> dict:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"mw": None, "heavy": None, "rings": None, "logp": None,
                    "tpsa": None, "rotatable": None, "hbd": None, "hba": None}
        return {
            "mw": round(Descriptors.MolWt(mol), 2),
            "heavy": mol.GetNumHeavyAtoms(),
            "rings": CalcNumRings(mol),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "tpsa": round(Descriptors.TPSA(mol), 2),
            "rotatable": Descriptors.NumRotatableBonds(mol),
            "hbd": Descriptors.NumHDonors(mol),
            "hba": Descriptors.NumHAcceptors(mol),
        }

    # ---------- Scaffold ----------
    @staticmethod
    def scaffold_info(smiles: str) -> dict:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"scaffold": None, "complexity": None, "novelty_tier": None}
        try:
            scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
        except Exception:
            scaffold = None
        # A simple applicability-domain proxy from ring count, heavy atoms and TPSA
        heavy = mol.GetNumHeavyAtoms()
        rings = CalcNumRings(mol)
        tpsa = Descriptors.TPSA(mol)
        # complexity 0..1 (Bertz-inspired, clipped)
        bertz = Descriptors.BertzCT(mol)
        complexity = max(0.0, min(1.0, bertz / 1000.0))
        # A rough "in-domain" score: drug-like molecules (heavy 10..40, rings 1..5) get high
        in_domain = 1.0
        if heavy < 6 or heavy > 60:
            in_domain -= 0.3
        if rings < 1 or rings > 6:
            in_domain -= 0.2
        if tpsa > 200:
            in_domain -= 0.2
        in_domain = max(0.05, min(1.0, in_domain))
        novelty_tier = "in-domain" if in_domain >= 0.8 else ("borderline" if in_domain >= 0.5 else "out-of-domain")
        return {
            "scaffold": scaffold or "",
            "complexity": round(complexity, 3),
            "applicability": round(in_domain, 3),
            "novelty_tier": novelty_tier,
        }

    # ---------- Confidence ----------
    @staticmethod
    def _reg_uncertainty(model, x: np.ndarray) -> Tuple[float, float]:
        """Estimate std-dev of prediction by chunk-averaging over tree slices.

        We split the ensemble into K disjoint chunks and use variance across the
        cumulative-partial predictions as a cheap uncertainty proxy.
        """
        # Access the sklearn wrapper's underlying booster
        try:
            booster = model.get_booster()
            n_trees = booster.num_boosted_rounds()
            if n_trees < 20:
                return 0.0, 0.0
            chunks = 6
            step = max(1, n_trees // chunks)
            preds = []
            for i in range(chunks):
                start = i * step
                end = (i + 1) * step if i < chunks - 1 else n_trees
                if end <= start:
                    continue
                # Predict using only trees in slice by requesting iteration_range on the sklearn model
                # sklearn XGBRegressor supports iteration_range in predict
                p = model.predict(x, iteration_range=(start, end))
                preds.append(float(p[0]))
            arr = np.array(preds, dtype=float)
            mu = float(arr.mean())
            sigma = float(arr.std())
            return mu, sigma
        except Exception as exc:
            logger.warning(f"Uncertainty calc failed: {exc}")
            # Fallback
            try:
                mu = float(model.predict(x)[0])
                return mu, 0.0
            except Exception:
                return 0.0, 0.0

    # ---------- Predict ----------
    def predict(self, smiles: str) -> dict:
        if not self.available:
            raise RuntimeError("No models loaded")
        x = self._fingerprint(smiles)
        out: dict = {}

        for key, model in self.models.items():
            meta = _ENDPOINT_META[key]
            if meta["task"] == "classification":
                proba = float(model.predict_proba(x)[0][1])
                # Bernoulli std for a single sample
                sigma = math.sqrt(max(0.0, proba * (1.0 - proba)))
                z = 1.28  # ~80% CI
                lo = max(0.0, proba - z * sigma / max(1.0, math.sqrt(50)))  # scaled
                hi = min(1.0, proba + z * sigma / max(1.0, math.sqrt(50)))
                # Confidence tier: further from 0.5 = higher confidence
                dist = abs(proba - 0.5) * 2  # 0..1
                if dist > 0.7:
                    tier = "high"
                elif dist > 0.3:
                    tier = "moderate"
                else:
                    tier = "low"
                out[key] = {
                    "label": meta["label"],
                    "category": meta["category"],
                    "code": meta["code"],
                    "type": "classification",
                    "probability": round(proba, 4),
                    "prediction": meta["positive"] if proba >= 0.5 else meta["negative"],
                    "ci_low": round(lo, 4),
                    "ci_high": round(hi, 4),
                    "confidence": tier,
                    "sigma": round(sigma, 4),
                }
            else:
                mu, sigma = self._reg_uncertainty(model, x)
                # 80% CI approx
                z = 1.28
                lo = mu - z * sigma
                hi = mu + z * sigma
                # scale is endpoint-dependent; use a rough scale
                scale = 6.0 if key == "Solubility" else 8.0
                tier = _confidence_tier(sigma, scale)
                out[key] = {
                    "label": meta["label"],
                    "category": meta["category"],
                    "code": meta["code"],
                    "type": "regression",
                    "value": round(mu, 4),
                    "unit": meta["unit"],
                    "ci_low": round(lo, 4),
                    "ci_high": round(hi, 4),
                    "confidence": tier,
                    "sigma": round(sigma, 4),
                }
        return out


# lazy singleton
_predictor: "AdmetPredictor | None" = None


def get_predictor() -> AdmetPredictor:
    global _predictor
    if _predictor is None:
        _predictor = AdmetPredictor()
    return _predictor


# ---------- Batch CSV helpers ----------

def parse_smiles_csv(content: bytes, max_rows: int = 500) -> List[dict]:
    """Parse an uploaded CSV file. Accepts columns 'smiles' (case-insensitive) or first column.

    Returns list of {row_idx, name, smiles}.
    """
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        text = content.decode("latin-1", errors="replace")
    text = text.strip()
    if not text:
        return []
    # Sniff delimiter
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t|")
    except Exception:
        dialect = csv.excel

    reader = csv.reader(io.StringIO(text), dialect=dialect)
    rows = list(reader)
    if not rows:
        return []

    header = [h.strip().lower() for h in rows[0]]
    has_header = any(h in header for h in ("smiles", "smile", "structure", "drug"))
    smiles_idx = 0
    name_idx = None
    start = 0
    if has_header:
        start = 1
        for want in ("smiles", "smile", "structure", "drug"):
            if want in header:
                smiles_idx = header.index(want)
                break
        for want in ("name", "id", "drug_id", "compound"):
            if want in header:
                name_idx = header.index(want)
                break

    out = []
    for i, row in enumerate(rows[start:start + max_rows]):
        if not row:
            continue
        s = row[smiles_idx].strip() if smiles_idx < len(row) else ""
        if not s:
            continue
        name = ""
        if name_idx is not None and name_idx < len(row):
            name = row[name_idx].strip()
        out.append({"row_idx": i + 1, "name": name, "smiles": s})
    return out


def results_to_csv(items: List[dict]) -> str:
    """Turn a batch response into a downloadable CSV string."""
    cols = [
        "row_idx", "name", "smiles", "mw", "heavy", "rings", "logp",
        "HIA_prob", "HIA_pred", "BBB_prob", "BBB_pred",
        "CYP2D6_prob", "CYP2D6_pred", "Solubility_logS", "VDss_Lkg", "error",
    ]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(cols)
    for it in items:
        r = it.get("results") or {}
        d = it.get("descriptors") or {}
        w.writerow([
            it.get("row_idx"),
            it.get("name") or "",
            it.get("smiles") or "",
            d.get("mw"),
            d.get("heavy"),
            d.get("rings"),
            d.get("logp"),
            r.get("HIA", {}).get("probability"),
            r.get("HIA", {}).get("prediction"),
            r.get("BBB", {}).get("probability"),
            r.get("BBB", {}).get("prediction"),
            r.get("CYP2D6", {}).get("probability"),
            r.get("CYP2D6", {}).get("prediction"),
            r.get("Solubility", {}).get("value"),
            r.get("VDss", {}).get("value"),
            it.get("error") or "",
        ])
    return buf.getvalue()
