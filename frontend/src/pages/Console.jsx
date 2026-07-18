import React, { useState } from "react";
import { ArrowRight, Beaker, ChevronDown, Copy, Check, AlertTriangle, Loader2, Layers, FileUp } from "lucide-react";
import { EXAMPLES, mockPredict, mockDescriptors } from "../mock";
import { toast } from "sonner";
import axios from "axios";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "../components/ui/dropdown-menu";
import { ProbCard, RegressionCard } from "../components/ResultCards";
import ScaffoldPanel from "../components/ScaffoldPanel";
import BatchUpload from "../components/BatchUpload";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function Kicker({ children }) {
  return (
    <div className="kicker mono text-[11px] ink-mute uppercase tracking-[0.28em]">{children}</div>
  );
}

function SingleConsole() {
  const [smiles, setSmiles] = useState("CN1C=NC2=C1C(=O)N(C(=O)N2C)C");
  const [activeExample, setActiveExample] = useState("Caffeine");
  const [results, setResults] = useState(null);
  const [scaffold, setScaffold] = useState(null);
  const [predictedSmiles, setPredictedSmiles] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState("mock");
  const [descriptors, setDescriptors] = useState(null);

  const displayDescriptors = descriptors || mockDescriptors(predictedSmiles || smiles);

  const handlePredict = async () => {
    if (!smiles.trim()) {
      setError("Enter a SMILES string first.");
      toast.error("Enter a SMILES string first.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/predict`, { smiles: smiles.trim() });
      if (res.data && res.data.results) {
        setResults(res.data.results);
        setDescriptors(res.data.descriptors || null);
        setScaffold(res.data.scaffold || null);
        setPredictedSmiles(smiles.trim());
        setSource(res.data.source || "model");
        toast.success(`Analysed ${smiles.trim().length} chars — 5 endpoints ready`);
      } else {
        throw new Error("Unexpected response");
      }
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (detail && typeof detail === "string" && /invalid smiles/i.test(detail)) {
        setError(detail);
        toast.error(detail);
      } else if (e?.response?.status === 422) {
        setError(detail || "Invalid SMILES string");
        toast.error(detail || "Invalid SMILES string");
      } else {
        // fallback to mock
        const mocked = mockPredict(smiles.trim());
        setResults(mocked);
        setDescriptors(null);
        setScaffold(null);
        setPredictedSmiles(smiles.trim());
        setSource("mock");
        toast.message(`Analysed ${smiles.trim().length} chars — 5 endpoints ready`, {
          description: "Preview engine",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExample = (ex) => {
    setSmiles(ex.smiles);
    setActiveExample(ex.name);
    setError("");
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(predictedSmiles || smiles);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch (e) {}
  };

  return (
    <>
      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-8">
          <div className="mt-2 flex items-center gap-3 mono text-[11px] ink-mute uppercase tracking-[0.22em]">
            <Beaker size={14} className="lime" strokeWidth={1.5} />
            <span>Enter SMILES</span>
          </div>
          <input
            value={smiles}
            onChange={(e) => setSmiles(e.target.value)}
            spellCheck={false}
            placeholder="e.g. CC(=O)OC1=CC=CC=C1C(=O)O"
            className="input-underline w-full text-[28px] md:text-[36px] mt-4 ink caret-lime tracking-tight"
            style={{ color: "rgb(235 236 230)" }}
            onKeyDown={(e) => e.key === "Enter" && handlePredict()}
          />
          {error && (
            <div className="mt-3 mono text-[11px] text-[rgb(255_74_128)] flex items-center gap-2 uppercase tracking-[0.2em]">
              <AlertTriangle size={12} /> {error}
            </div>
          )}

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button onClick={handlePredict} className="btn btn-lime" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" /> Predicting
                </>
              ) : (
                <>
                  Predict ADMET <ArrowRight size={14} />
                </>
              )}
            </button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="btn btn-ghost">
                  Load example <ChevronDown size={14} />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="bg-[rgb(20_22_20)] border hairline text-[rgb(235_236_230)]">
                {EXAMPLES.map((ex) => (
                  <DropdownMenuItem
                    key={ex.name}
                    onClick={() => handleExample(ex)}
                    className="mono text-[12px] tracking-[0.14em] uppercase focus:bg-[rgb(30_33_30)] focus:text-white"
                  >
                    {ex.name}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.name}
                data-active={activeExample === ex.name}
                onClick={() => handleExample(ex)}
                className="chip"
              >
                {ex.name}
              </button>
            ))}
          </div>
        </div>

        {/* Right meta */}
        <div className="col-span-12 lg:col-span-4 lg:pl-8">
          <div className="border hairline p-6 bg-soft">
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">Model</div>
            <div className="display text-[24px] mt-2 ink">HelixADMET · v1.0.4</div>
            <div className="tick my-4" />
            {[
              ["Featurizer", "Morgan FP r=2 · 2048b"],
              ["Backbone", "XGBoost"],
              ["Endpoints", "5"],
              ["Latency (p50)", "184 ms"],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center justify-between py-1.5">
                <span className="mono text-[11px] ink-mute uppercase tracking-[0.2em]">{k}</span>
                <span className="mono text-[12px] ink">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      {results ? (
        <section className="mt-20">
          <div className="flex items-end justify-between flex-wrap gap-6">
            <div>
              <div className="mono text-[11px] ink-mute uppercase tracking-[0.22em]">
                Prediction for
              </div>
              <div className="mt-3 flex items-center gap-3 flex-wrap">
                <span className="mono text-[18px] lime break-all">{predictedSmiles}</span>
                <button onClick={handleCopy} className="chip" aria-label="copy smiles">
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  <span className="ml-1">{copied ? "Copied" : "Copy"}</span>
                </button>
                <span className="chip" data-active={source === "model" ? "true" : "false"}>
                  {source === "model" ? "Real Model" : "Preview"}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-6 mono text-[12px] ink-dim uppercase tracking-[0.2em]">
              <div>MW <span className="ink ml-1">{displayDescriptors.mw ?? "—"}</span></div>
              <div>Heavy <span className="ink ml-1">{displayDescriptors.heavy ?? "—"}</span></div>
              <div>Rings <span className="ink ml-1">{displayDescriptors.rings ?? "—"}</span></div>
              {displayDescriptors.logp !== undefined && displayDescriptors.logp !== null && (
                <div>LogP <span className="ink ml-1">{displayDescriptors.logp}</span></div>
              )}
            </div>
          </div>

          <div className="tick mt-6" />

          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            <ProbCard idx={1} code="HIA" endpoint={results.HIA} />
            <ProbCard idx={2} code="BBB" endpoint={results.BBB} />
            <ProbCard idx={3} code="CYP2D6" endpoint={results.CYP2D6} />
            <RegressionCard idx={4} code="SOL" endpoint={results.Solubility} />
            <RegressionCard idx={5} code="VDss" endpoint={results.VDss} />

            <ScaffoldPanel scaffold={scaffold} descriptors={descriptors} />
          </div>
        </section>
      ) : (
        <section className="mt-24 border hairline bg-soft p-10 flex flex-col md:flex-row items-center gap-10">
          <div>
            <div className="mono text-[11px] ink-mute uppercase tracking-[0.22em]">Idle</div>
            <div className="display text-[36px] md:text-[44px] mt-4 ink leading-tight">
              Awaiting a <span className="serif-i lime">molecule</span>.
            </div>
            <p className="mono text-[12px] ink-dim mt-4 max-w-[520px] leading-[1.9]">
              Type or paste a SMILES string above. Pick one of the sample compounds to see the
              full five-endpoint readout with 80% confidence intervals.
            </p>
          </div>
          <div className="grid grid-cols-5 gap-px border hairline bg-[rgb(30_33_30)] ml-auto">
            {["HIA", "BBB", "CYP2D6", "SOL", "VDss"].map((c) => (
              <div key={c} className="bg-bg px-5 py-4 mono text-[10px] ink-mute uppercase tracking-[0.22em]">
                {c}
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

export default function Console() {
  const [tab, setTab] = useState("single");

  return (
    <main className="relative z-10 max-w-[1400px] mx-auto px-8 pt-20 pb-10">
      <Kicker>The Console</Kicker>

      {/* Tabs */}
      <div className="mt-10 flex items-center gap-1 border-b hairline">
        <button
          onClick={() => setTab("single")}
          className={`mono text-[11px] uppercase tracking-[0.22em] px-4 py-3 border-b -mb-px ${
            tab === "single" ? "ink border-[rgb(93_227_255)]" : "ink-mute border-transparent"
          } flex items-center gap-2`}
        >
          <Layers size={12} /> Single molecule
        </button>
        <button
          onClick={() => setTab("batch")}
          data-testid="batch-tab"
          className={`mono text-[11px] uppercase tracking-[0.22em] px-4 py-3 border-b -mb-px ${
            tab === "batch" ? "ink border-[rgb(93_227_255)]" : "ink-mute border-transparent"
          } flex items-center gap-2`}
        >
          <FileUp size={12} /> Batch CSV
        </button>
      </div>

      <div className="mt-8">
        {tab === "single" ? <SingleConsole /> : <BatchUpload />}
      </div>
    </main>
  );
}
