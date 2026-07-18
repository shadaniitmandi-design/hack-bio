import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowDown, ArrowUpRight, ChevronRight } from "lucide-react";
import { MODEL_META } from "../mock";

const HERO_IMG =
  "https://images.unsplash.com/photo-1663798047884-2d1c24a53611?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NzV8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGZsb3dpbmclMjByaWJib24lMjBkYXJrfGVufDB8fHxncmVlbnwxNzg0NDA3Njk5fDA&ixlib=rb-4.1.0&q=85";

const LOWER_IMG =
  "https://images.unsplash.com/photo-1634976276568-9ea10353a8cd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NDh8MHwxfHNlYXJjaHwzfHxldGhlcmVhbCUyMGdyZWVuJTIwd2F2ZXxlbnwwfHx8Z3JlZW58MTc4NDQwNzY5OXww&ixlib=rb-4.1.0&q=85";

function TickerRow() {
  const items = [
    "HIA · ROC-AUC 0.891",
    "BBB · ROC-AUC 0.904",
    "CYP2D6 · ROC-AUC 0.842",
    "Solubility · R² 0.781",
    "VDss · R² 0.612",
    "Morgan Fingerprints · 2048 bits",
    "Scaffold-split · zero leakage",
    "XGBoost · 300 estimators",
  ];
  const line = [...items, ...items];
  return (
    <div className="overflow-hidden border-y hairline py-4">
      <div className="flex marquee whitespace-nowrap gap-14 mono text-[12px] ink-dim tracking-[0.2em] uppercase">
        {line.map((t, i) => (
          <span key={i} className="flex items-center gap-14">
            <span>{t}</span>
            <span className="lime">•</span>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function Landing() {
  const nav = useNavigate();

  return (
    <main className="relative z-10">
      {/* Hero */}
      <section className="max-w-[1400px] mx-auto px-8 pt-24 pb-20 grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-7">
          <div className="kicker mono text-[11px] ink-mute uppercase tracking-[0.28em]">
            ADMET Intelligence Engine
          </div>
          <h1 className="display mt-8 text-[64px] md:text-[84px] xl:text-[92px] leading-[0.92] font-extrabold ink">
            DECODE
            <br />
            MOLECULAR
            <br />
            DESTINY <span className="serif-i lime font-normal text-[52px] md:text-[68px] xl:text-[76px] whitespace-nowrap">in one string</span>
          </h1>
          <p className="mono ink-dim mt-10 max-w-[520px] text-[13px] leading-[1.9] tracking-[0.02em]">
            Paste a SMILES string. Our engine returns five ADMET endpoints — blood-brain barrier,
            CYP2D6 inhibition, aqueous solubility, intestinal absorption and volume of distribution —
            in under a second.
          </p>
          <div className="mt-10 flex items-center gap-4">
            <button onClick={() => nav("/predict")} className="btn btn-lime">
              Run a prediction <ArrowDown size={14} strokeWidth={2} />
            </button>
            <button onClick={() => nav("/pipeline")} className="btn btn-ghost">
              How it works <ChevronRight size={14} strokeWidth={2} />
            </button>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 relative">
          <div className="relative border hairline p-4 bg-soft floaty ring-cyan">
            <img
              src={HERO_IMG}
              alt="Conformational space visualization"
              className="w-full h-[420px] object-cover"
              style={{ filter: "hue-rotate(60deg) saturate(1.05) brightness(0.9) contrast(1.1)" }}
            />
            <div className="absolute inset-4 pointer-events-none border hairline-soft mix-blend-overlay" />
            <div className="flex items-center justify-between mt-3 mono text-[11px] ink-mute uppercase tracking-[0.22em]">
              <span>Fig. 01</span>
              <span>Conformational Space</span>
            </div>
          </div>

          {/* small numeric overlay */}
          <div className="hidden lg:block absolute -bottom-10 -left-10 border hairline bg-bg p-4 w-[220px]">
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">Latency</div>
            <div className="display text-[36px] leading-none mt-2 ink">
              184<span className="ink-mute text-[16px] mono ml-1">ms</span>
            </div>
            <div className="mono text-[10px] ink-dim mt-2">p50 · 5 endpoints</div>
          </div>
        </div>
      </section>

      <TickerRow />

      {/* Endpoints Grid */}
      <section className="max-w-[1400px] mx-auto px-8 pt-24">
        <div className="flex items-end justify-between mb-10">
          <div>
            <div className="kicker mono text-[11px] ink-mute uppercase tracking-[0.28em]">
              The Endpoints
            </div>
            <h2 className="display mt-6 text-[44px] md:text-[56px] font-bold ink leading-[1.02] max-w-[720px]">
              Five decisions your <span className="serif-i lime font-normal">molecule</span> can’t hide from.
            </h2>
          </div>
          <div className="mono text-[11px] ink-mute uppercase tracking-[0.22em] hidden md:block">
            v1.0.4 — Jul 2026
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-px border hairline bg-[rgb(30_33_30)]">
          {MODEL_META.endpoints.map((e, i) => (
            <div key={e.code} className="bg-bg p-6 min-h-[220px] flex flex-col justify-between hover:bg-soft transition-colors">
              <div>
                <div className="mono text-[10px] ink-mute tracking-[0.22em] uppercase">
                  0{i + 1} / {e.code}
                </div>
                <div className="mt-8 display text-[22px] leading-tight ink">{e.name}</div>
              </div>
              <div className="mt-6">
                <div className="tick mb-3" />
                <div className="flex items-baseline justify-between">
                  <span className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">{e.metric}</span>
                  <span className="display text-[24px] ink">{e.score.toFixed(3)}</span>
                </div>
                <div className="mono text-[10px] ink-mute mt-2 tracking-[0.15em] uppercase">{e.source}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Split feature */}
      <section className="max-w-[1400px] mx-auto px-8 pt-28 grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-5">
          <img src={LOWER_IMG} alt="molecular flow" className="w-full h-[500px] object-cover border hairline" style={{ filter: "hue-rotate(60deg) saturate(1.05) brightness(0.9) contrast(1.05)" }} />
          <div className="mono text-[11px] ink-mute uppercase tracking-[0.22em] mt-3 flex justify-between">
            <span>Fig. 02</span><span>Latent Manifold</span>
          </div>
        </div>
        <div className="col-span-12 lg:col-span-7 lg:pl-12">
          <div className="kicker mono text-[11px] ink-mute uppercase tracking-[0.28em]">The Method</div>
          <h3 className="display text-[40px] md:text-[52px] mt-6 ink leading-[1.05] font-bold">
            Fingerprints in. <span className="serif-i lime font-normal">Failures out.</span>
          </h3>
          <p className="mono ink-dim mt-8 leading-[1.9] text-[13px] max-w-[640px]">
            We hash every molecule into a 2048-bit Morgan fingerprint, radius 2. A stack of
            gradient-boosted trees — one per endpoint — votes on absorption, distribution and
            metabolic fate. All test folds are scaffold-split, so nothing familiar leaks into
            evaluation.
          </p>
          <div className="mt-10 grid grid-cols-2 gap-px border hairline bg-[rgb(30_33_30)]">
            {[
              { k: "Featurizer", v: "Morgan FP r=2" },
              { k: "Bits", v: "2048" },
              { k: "Backbone", v: "XGBoost" },
              { k: "Split", v: "Bemis-Murcko" },
              { k: "Endpoints", v: "5 (A / D / M)" },
              { k: "Training", v: "TDC ADME" },
            ].map((row) => (
              <div key={row.k} className="bg-bg p-4 flex items-center justify-between">
                <span className="mono text-[11px] ink-mute uppercase tracking-[0.22em]">{row.k}</span>
                <span className="mono text-[12px] ink">{row.v}</span>
              </div>
            ))}
          </div>

          <button onClick={() => nav("/predict")} className="btn btn-ghost mt-10">
            Try it now <ArrowUpRight size={14} />
          </button>
        </div>
      </section>
    </main>
  );
}
