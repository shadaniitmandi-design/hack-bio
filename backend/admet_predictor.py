"""ADMET predictor - loads XGBoost models trained on TDC datasets.

Model source: https://github.com/Mannatkathuria/SMILES_TO_ADMET
Featurizer: Morgan fingerprints (radius=2, 2048 bits)
"""

import os
import logging
from pathlib import Path

import joblib
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
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

    @staticmethod
    def _fingerprint(smiles: str) -> np.ndarray:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES string")
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        arr = np.zeros(2048, dtype=np.int8)
        ConvertToNumpyArray(fp, arr)
        return arr.reshape(1, -1)

    @staticmethod
    def descriptors(smiles: str) -> dict:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"mw": None, "heavy": None, "rings": None, "logp": None}
        return {
            "mw": round(Descriptors.MolWt(mol), 2),
            "heavy": mol.GetNumHeavyAtoms(),
            "rings": Chem.rdMolDescriptors.CalcNumRings(mol),
            "logp": round(Descriptors.MolLogP(mol), 2),
        }

    def predict(self, smiles: str) -> dict:
        if not self.available:
            raise RuntimeError("No models loaded")
        x = self._fingerprint(smiles)
        out: dict = {}

        for key, model in self.models.items():
            meta = _ENDPOINT_META[key]
            if meta["task"] == "classification":
                proba = float(model.predict_proba(x)[0][1])
                out[key] = {
                    "label": meta["label"],
                    "category": meta["category"],
                    "code": meta["code"],
                    "type": "classification",
                    "probability": round(proba, 4),
                    "prediction": meta["positive"] if proba >= 0.5 else meta["negative"],
                }
            else:
                value = float(model.predict(x)[0])
                out[key] = {
                    "label": meta["label"],
                    "category": meta["category"],
                    "code": meta["code"],
                    "type": "regression",
                    "value": round(value, 4),
                    "unit": meta["unit"],
                }
        return out


# lazy singleton
_predictor: AdmetPredictor | None = None


def get_predictor() -> AdmetPredictor:
    global _predictor
    if _predictor is None:
        _predictor = AdmetPredictor()
    return _predictor
