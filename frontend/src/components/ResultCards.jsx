import React from "react";
import CircularMeter from "./CircularMeter";
import { fmtPct, fmtNum, classFromProb, solubilityTone } from "../lib/format";

function ConfidenceRow({ tier }) {
  const map = {
    high: { label: "HIGH CONFIDENCE", cls: "lime", bar: "bg-[rgb(210_255_62)]" },
    moderate: { label: "MODERATE CONFIDENCE", cls: "text-[rgb(255_176_66)]", bar: "bg-[rgb(255_176_66)]" },
    low: { label: "LOW CONFIDENCE", cls: "text-[rgb(255_74_128)]", bar: "bg-[rgb(255_74_128)]" },
  };
  const t = map[tier] || map.moderate;
  const width = tier === "high" ? "w-full" : tier === "moderate" ? "w-2/3" : "w-1/3";
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mono text-[9px] uppercase tracking-[0.22em] ink-mute">
        <span>Confidence</span>
        <span className={t.cls}>{t.label}</span>
      </div>
      <div className="mt-2 h-[3px] w-full bg-[rgb(30_33_30)] overflow-hidden">
        <div className={`h-full ${t.bar} ${width}`} />
      </div>
    </div>
  );
}

function CIStrip({ lo, hi, value, min, max, tone }) {
  const clamp = (v) => Math.max(min, Math.min(max, v));
  const range = max - min || 1;
  const l = ((clamp(lo) - min) / range) * 100;
  const h = ((clamp(hi) - min) / range) * 100;
  const p = ((clamp(value) - min) / range) * 100;
  const color = tone === "lime" ? "rgb(210 255 62)" : tone === "warn" ? "rgb(255 176 66)" : "rgb(255 74 128)";
  return (
    <div className="mt-4">
      <div className="relative h-[6px] w-full bg-[rgb(30_33_30)]">
        <div className="absolute h-full" style={{ left: `${l}%`, width: `${Math.max(2, h - l)}%`, background: color, opacity: 0.28 }} />
        <div className="absolute h-full w-[2px]" style={{ left: `calc(${p}% - 1px)`, background: color }} />
      </div>
      <div className="flex justify-between mono text-[9px] uppercase tracking-[0.2em] ink-mute mt-1.5">
        <span>{fmtNum(lo, 2)}</span>
        <span>80% CI</span>
        <span>{fmtNum(hi, 2)}</span>
      </div>
    </div>
  );
}

export function ProbCard({ code, idx, endpoint }) {
  const { probability, prediction, label, category, ci_low, ci_high, confidence } = endpoint;
  const cls = classFromProb(probability);
  const tone = cls.tone === "good" ? "lime" : cls.tone === "warn" ? "warn" : "pink";
  const toneText = cls.tone === "good" ? "lime" : cls.tone === "warn" ? "text-[rgb(255_176_66)]" : "text-[rgb(255_74_128)]";
  return (
    <div className="bg-bg p-7 min-h-[300px] flex flex-col justify-between border hairline">
      <div className="flex items-start justify-between">
        <div>
          <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">
            {String(idx).padStart(2, "0")} / {code}
          </div>
          <div className="display text-[22px] mt-4 ink leading-tight">{label}</div>
          <div className="mono text-[10px] ink-mute uppercase tracking-[0.2em] mt-1">{category}</div>
        </div>
        <CircularMeter value={probability} tone={tone} size={92} thickness={5} />
      </div>
      <div>
        <div className="tick my-4" />
        <div className="flex items-end justify-between">
          <div>
            <div className="display text-[44px] leading-none ink">{fmtPct(probability)}</div>
            <div className="mono text-[10px] ink-mute mt-1 uppercase tracking-[0.2em]">probability</div>
          </div>
          <div className={`inline-flex items-center border hairline px-3 py-1 mono text-[10px] uppercase tracking-[0.22em] ${toneText}`}>
            {prediction}
          </div>
        </div>
        {ci_low !== undefined && ci_high !== undefined && (
          <CIStrip lo={ci_low} hi={ci_high} value={probability} min={0} max={1} tone={tone} />
        )}
        <ConfidenceRow tier={confidence} />
      </div>
    </div>
  );
}

export function RegressionCard({ code, idx, endpoint }) {
  const { value, unit, label, category, ci_low, ci_high, confidence } = endpoint;
  const tone = code === "SOL" ? solubilityTone(value) : classFromProb(Math.min(1, Math.max(0, value / 10)));
  const toneText = tone.tone === "good" ? "lime" : tone.tone === "warn" ? "text-[rgb(255_176_66)]" : "text-[rgb(255_74_128)]";
  const toneKey = tone.tone === "good" ? "lime" : tone.tone === "warn" ? "warn" : "pink";
  // Reasonable axis ranges for each endpoint
  const axis = code === "SOL" ? { min: -10, max: 2 } : { min: 0, max: 15 };
  return (
    <div className="bg-bg p-7 min-h-[300px] flex flex-col justify-between border hairline">
      <div className="flex items-start justify-between">
        <div>
          <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">
            {String(idx).padStart(2, "0")} / {code}
          </div>
          <div className="display text-[22px] mt-4 ink leading-tight">{label}</div>
          <div className="mono text-[10px] ink-mute uppercase tracking-[0.2em] mt-1">{category}</div>
        </div>
        <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em] px-2 py-1 border hairline">regression</div>
      </div>
      <div>
        <div className="tick my-4" />
        <div className="flex items-end justify-between">
          <div>
            <div className="display text-[44px] leading-none ink">{fmtNum(value, 2)}</div>
            <div className="mono text-[10px] ink-mute mt-1 uppercase tracking-[0.2em]">{unit}</div>
          </div>
          <div className={`inline-flex items-center border hairline px-3 py-1 mono text-[10px] uppercase tracking-[0.22em] ${toneText}`}>
            {tone.label}
          </div>
        </div>
        {ci_low !== undefined && ci_high !== undefined && (
          <CIStrip lo={ci_low} hi={ci_high} value={value} min={axis.min} max={axis.max} tone={toneKey} />
        )}
        <ConfidenceRow tier={confidence} />
      </div>
    </div>
  );
}
