import React, { useEffect, useState } from "react";

export default function CircularMeter({ value = 0.5, tone = "lime", size = 120, thickness = 6, label }) {
  // value: 0..1
  const [v, setV] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setV(value), 60);
    return () => clearTimeout(t);
  }, [value]);

  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.max(0, Math.min(1, v)));

  const color =
    tone === "lime"
      ? "rgb(210 255 62)"
      : tone === "pink"
      ? "rgb(255 74 128)"
      : tone === "warn"
      ? "rgb(255 176 66)"
      : "rgb(210 255 62)";

  return (
    <div className="relative inline-block" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgb(38 42 38)" strokeWidth={thickness} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={color}
          strokeWidth={thickness}
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={off}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      {label && (
        <div className="absolute inset-0 flex items-center justify-center mono text-[10px] ink-mute tracking-[0.14em]">
          {label}
        </div>
      )}
    </div>
  );
}
