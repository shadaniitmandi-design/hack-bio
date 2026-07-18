import React from "react";
import { Fingerprint, Sparkles, Copy, Check } from "lucide-react";
import { useState } from "react";

export default function ScaffoldPanel({ scaffold, descriptors }) {
  const [copied, setCopied] = useState(false);
  if (!scaffold) return null;
  const tier = scaffold.novelty_tier || "in-domain";
  const tierMap = {
    "in-domain": { cls: "lime", copy: "Within drug-like domain" },
    borderline: { cls: "text-[rgb(255_176_66)]", copy: "Borderline domain" },
    "out-of-domain": { cls: "text-[rgb(255_74_128)]", copy: "Out-of-domain molecule" },
  };
  const t = tierMap[tier] || tierMap["in-domain"];
  const copy = async () => {
    if (!scaffold.scaffold) return;
    try {
      await navigator.clipboard.writeText(scaffold.scaffold);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch (e) {}
  };

  return (
    <div className="border hairline p-7 bg-soft min-h-[300px] flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-3 mono text-[10px] ink-mute uppercase tracking-[0.22em]">
          <Fingerprint size={14} className="lime" strokeWidth={1.5} />
          Scaffold
        </div>
        <div className="display text-[22px] ink mt-4 leading-tight">Bemis–Murcko backbone</div>
        <div className="tick my-4" />
        <div className="mono text-[12px] ink break-all">
          {scaffold.scaffold || <span className="ink-mute">acyclic — no ring scaffold</span>}
        </div>
        {scaffold.scaffold && (
          <button onClick={copy} className="chip mt-4">
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span className="ml-1">{copied ? "Copied" : "Copy scaffold"}</span>
          </button>
        )}
      </div>
      <div className="mt-6">
        <div className="flex items-center justify-between mono text-[10px] uppercase tracking-[0.22em]">
          <span className="ink-mute flex items-center gap-2"><Sparkles size={12} /> Applicability</span>
          <span className={t.cls}>{t.copy}</span>
        </div>
        <div className="tick mt-3" />
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.2em]">TPSA</div>
            <div className="display text-[20px] ink mt-1">{descriptors?.tpsa ?? "—"}</div>
          </div>
          <div>
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.2em]">Rot. Bonds</div>
            <div className="display text-[20px] ink mt-1">{descriptors?.rotatable ?? "—"}</div>
          </div>
          <div>
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.2em]">HBD / HBA</div>
            <div className="display text-[20px] ink mt-1">
              {(descriptors?.hbd ?? "—")} / {(descriptors?.hba ?? "—")}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
