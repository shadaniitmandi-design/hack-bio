export function fmtPct(p) {
  return `${Math.round(p * 100)}%`;
}

export function fmtNum(n, d = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return Number(n).toFixed(d);
}

export function classFromProb(p) {
  if (p >= 0.75) return { tone: "good", label: "HIGH" };
  if (p >= 0.5) return { tone: "warn", label: "MODERATE" };
  return { tone: "bad", label: "LOW" };
}

export function solubilityTone(logS) {
  // more negative = less soluble
  if (logS > -2) return { tone: "good", label: "HIGH" };
  if (logS > -4) return { tone: "warn", label: "MODERATE" };
  return { tone: "bad", label: "LOW" };
}
