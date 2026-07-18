// Mock ADMET predictions - will be replaced by backend once model is wired

export const EXAMPLES = [
  { name: "Aspirin", smiles: "CC(=O)OC1=CC=CC=C1C(=O)O" },
  { name: "Caffeine", smiles: "CN1C=NC2=C1C(=O)N(C(=O)N2C)C" },
  { name: "Ibuprofen", smiles: "CC(C)Cc1ccc(cc1)C(C)C(=O)O" },
  { name: "Paracetamol", smiles: "CC(=O)Nc1ccc(O)cc1" },
  { name: "Ethanol", smiles: "CCO" },
];

// Deterministic pseudo-random from string, so mock feels stable per SMILES
function seedFromString(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return () => {
    h += 0x6d2b79f5;
    let t = h;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mockDescriptors(smiles) {
  // very rough & fun mock: weight ~ chars, heavy atoms ~ uppercase C/N/O count
  const s = smiles || "";
  const heavy = (s.match(/[CNOSFPnos]/g) || []).length;
  const rings = (s.match(/[0-9]/g) || []).length / 2;
  const mw = Math.round(heavy * 12 + s.length * 1.5 + 20);
  return {
    mw,
    heavy,
    rings: Math.max(1, Math.round(rings)),
  };
}

export function mockPredict(smiles) {
  const rand = seedFromString(smiles || "x");
  const hia = rand();
  const bbb = rand();
  const cyp = rand();
  const sol = -1 - rand() * 6; // logS -1 to -7
  const vdss = 0.2 + rand() * 8; // L/kg

  return {
    HIA: {
      label: "Human Intestinal Absorption",
      category: "Absorption",
      code: "HIA",
      type: "classification",
      probability: hia,
      prediction: hia >= 0.5 ? "High Absorption" : "Low Absorption",
    },
    BBB: {
      label: "Blood-Brain Barrier",
      category: "Distribution",
      code: "BBB",
      type: "classification",
      probability: bbb,
      prediction: bbb >= 0.5 ? "BBB Permeable" : "BBB Non-Permeable",
    },
    CYP2D6: {
      label: "CYP2D6 Inhibition",
      category: "Metabolism",
      code: "CYP2D6",
      type: "classification",
      probability: cyp,
      prediction: cyp >= 0.5 ? "CYP2D6 Inhibitor" : "CYP2D6 Non-Inhibitor",
    },
    Solubility: {
      label: "Aqueous Solubility",
      category: "Absorption",
      code: "SOL",
      type: "regression",
      value: sol,
      unit: "logS (mol/L)",
    },
    VDss: {
      label: "Volume of Distribution",
      category: "Distribution",
      code: "VDss",
      type: "regression",
      value: vdss,
      unit: "L/kg",
    },
  };
}

export const MODEL_META = {
  version: "v1.0.4",
  featurizer: "Morgan Fingerprints · r=2 · 2048 bits",
  backbone: "XGBoost · scaffold split",
  endpoints: [
    { code: "HIA", name: "Human Intestinal Absorption", task: "classification", metric: "ROC-AUC", score: 0.891, source: "TDC · HIA_Hou" },
    { code: "BBB", name: "Blood-Brain Barrier", task: "classification", metric: "ROC-AUC", score: 0.904, source: "TDC · BBB_Martins" },
    { code: "CYP2D6", name: "CYP2D6 Inhibition", task: "classification", metric: "ROC-AUC", score: 0.842, source: "TDC · CYP2D6_Veith" },
    { code: "SOL", name: "Aqueous Solubility", task: "regression", metric: "R²", score: 0.781, source: "TDC · AqSolDB" },
    { code: "VDss", name: "Volume of Distribution", task: "regression", metric: "R²", score: 0.612, source: "TDC · VDss_Lombardo" },
  ],
};
