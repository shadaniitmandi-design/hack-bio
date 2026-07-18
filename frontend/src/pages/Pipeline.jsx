import React from "react";
import { MODEL_META } from "../mock";
import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

function Kicker({ children }) {
  return <div className="kicker mono text-[11px] ink-mute uppercase tracking-[0.28em]">{children}</div>;
}

const STEPS = [
  {
    n: "01",
    title: "Ingest",
    body: "A SMILES string enters the pipeline. We normalise it with RDKit — canonicalise atoms, strip salts, reject malformed structures.",
  },
  {
    n: "02",
    title: "Featurize",
    body: "Every molecule is hashed into a 2048-bit Morgan fingerprint at radius 2 — capturing local chemical neighbourhoods around every atom.",
  },
  {
    n: "03",
    title: "Predict",
    body: "Five gradient-boosted tree ensembles score the molecule in parallel. Three classifiers, two regressors, one shared feature space.",
  },
  {
    n: "04",
    title: "Report",
    body: "Endpoints are returned with calibrated probabilities and confidence tags. Everything runs in under 200 ms on CPU.",
  },
];

export default function Pipeline() {
  const nav = useNavigate();
  return (
    <main className="relative z-10 max-w-[1400px] mx-auto px-8 pt-20 pb-10">
      <Kicker>The Pipeline</Kicker>
      <h1 className="display text-[56px] md:text-[80px] font-extrabold ink mt-8 leading-[0.98] max-w-[1100px]">
        From string to <span className="serif-i lime font-normal">signal</span>, in four hops.
      </h1>

      <div className="mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px border hairline bg-[rgb(30_33_30)]">
        {STEPS.map((s) => (
          <div key={s.n} className="bg-bg p-8 min-h-[260px]">
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">Step {s.n}</div>
            <div className="display text-[28px] ink mt-6">{s.title}</div>
            <div className="tick my-4" />
            <p className="mono text-[12px] ink-dim leading-[1.9]">{s.body}</p>
          </div>
        ))}
      </div>

      <section className="mt-24 grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-5">
          <Kicker>Benchmarks</Kicker>
          <h2 className="display text-[42px] md:text-[52px] ink mt-6 leading-[1.05] font-bold">
            Scaffold splits, honest scores.
          </h2>
          <p className="mono text-[12px] ink-dim mt-6 leading-[1.9] max-w-[440px]">
            Random splits over-count what a model “knows.” We split by Bemis-Murcko scaffold
            — so every test molecule looks unfamiliar to the ensemble. Metrics below are held-out.
          </p>
        </div>
        <div className="col-span-12 lg:col-span-7">
          <div className="border hairline">
            <div className="grid grid-cols-5 gap-px bg-[rgb(30_33_30)]">
              {["Endpoint", "Category", "Task", "Metric", "Score"].map((h) => (
                <div key={h} className="bg-bg px-4 py-3 mono text-[10px] ink-mute uppercase tracking-[0.22em]">
                  {h}
                </div>
              ))}
            </div>
            {MODEL_META.endpoints.map((e, i) => (
              <div key={e.code} className="grid grid-cols-5 gap-px bg-[rgb(30_33_30)] border-t hairline-soft">
                <div className="bg-bg px-4 py-5 ink mono text-[12px]">{e.name}</div>
                <div className="bg-bg px-4 py-5 ink-dim mono text-[12px]">
                  {i < 3 ? ["Absorption", "Distribution", "Metabolism"][i] : i === 3 ? "Absorption" : "Distribution"}
                </div>
                <div className="bg-bg px-4 py-5 ink-dim mono text-[12px] capitalize">{e.task}</div>
                <div className="bg-bg px-4 py-5 ink-dim mono text-[12px]">{e.metric}</div>
                <div className="bg-bg px-4 py-5 lime display text-[20px]">{e.score.toFixed(3)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-24 border hairline p-10 bg-soft flex flex-col md:flex-row items-start md:items-center gap-10 justify-between">
        <div>
          <Kicker>Ready?</Kicker>
          <h3 className="display text-[36px] md:text-[44px] ink mt-4 leading-tight">
            Put a molecule through the pipeline.
          </h3>
        </div>
        <button onClick={() => nav("/predict")} className="btn btn-lime">
          Open the console <ArrowRight size={14} />
        </button>
      </section>
    </main>
  );
}
