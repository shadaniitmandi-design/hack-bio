import React, { useRef, useState } from "react";
import axios from "axios";
import { Upload, Download, FileText, AlertTriangle, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { fmtNum, fmtPct } from "../lib/format";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SAMPLE_CSV = `smiles,name
CC(=O)OC1=CC=CC=C1C(=O)O,Aspirin
CN1C=NC2=C1C(=O)N(C(=O)N2C)C,Caffeine
CC(C)Cc1ccc(cc1)C(C)C(=O)O,Ibuprofen
CC(=O)Nc1ccc(O)cc1,Paracetamol
CCO,Ethanol
`;

export default function BatchUpload() {
  const fileRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [batch, setBatch] = useState(null); // {items, ok, failed, latency_ms}
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");

  const onPick = () => fileRef.current?.click();

  const upload = async (file) => {
    if (!file) return;
    setError("");
    setFileName(file.name);
    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await axios.post(`${API}/predict/batch/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setBatch(res.data);
      toast.success(`Predicted ${res.data.ok}/${res.data.count} molecules in ${res.data.latency_ms} ms`);
    } catch (e) {
      const detail = e?.response?.data?.detail || e.message;
      setError(typeof detail === "string" ? detail : "Upload failed");
      toast.error(typeof detail === "string" ? detail : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const onFile = (e) => {
    const file = e.target.files?.[0];
    upload(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) upload(file);
  };

  const downloadSample = () => {
    const blob = new Blob([SAMPLE_CSV], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sample_molecules.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportCsv = async () => {
    if (!batch?.items?.length) return;
    try {
      const res = await axios.post(`${API}/predict/batch/export`, { items: batch.items }, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `helixadmet_${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error("Could not export CSV");
    }
  };

  const reset = () => {
    setBatch(null);
    setError("");
    setFileName("");
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <section className="mt-2">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Drop zone */}
        <div className="lg:col-span-8">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            className="border border-dashed hairline p-10 bg-soft flex flex-col items-center justify-center text-center min-h-[220px]"
          >
            <Upload size={22} className="lime" strokeWidth={1.5} />
            <div className="display text-[24px] mt-4 ink">Drop a CSV of SMILES</div>
            <div className="mono text-[11px] ink-mute mt-2 uppercase tracking-[0.2em]">
              Column: <span className="ink">smiles</span> · optional: <span className="ink">name</span> · max 500 rows / 2 MB
            </div>
            <div className="mt-6 flex flex-wrap items-center gap-3 justify-center">
              <button onClick={onPick} className="btn btn-lime" disabled={loading}>
                {loading ? (<><Loader2 size={14} className="animate-spin" /> Predicting</>) : (<><Upload size={14} /> Choose file</>)}
              </button>
              <button onClick={downloadSample} className="btn btn-ghost">
                <FileText size={14} /> Sample CSV
              </button>
              {batch && (
                <button onClick={reset} className="btn btn-ghost">
                  <X size={14} /> Reset
                </button>
              )}
            </div>
            <input ref={fileRef} type="file" accept=".csv,text/csv" onChange={onFile} className="hidden" />
            {fileName && (
              <div className="mono text-[11px] ink-mute mt-4 uppercase tracking-[0.2em]">Uploaded: <span className="ink">{fileName}</span></div>
            )}
            {error && (
              <div className="mt-4 mono text-[11px] text-[rgb(255_74_128)] flex items-center gap-2 uppercase tracking-[0.2em]">
                <AlertTriangle size={12} /> {error}
              </div>
            )}
          </div>
        </div>

        {/* Meta panel */}
        <div className="lg:col-span-4">
          <div className="border hairline p-6 bg-soft">
            <div className="mono text-[10px] ink-mute uppercase tracking-[0.22em]">Batch Summary</div>
            <div className="tick my-4" />
            {batch ? (
              <>
                <div className="flex items-center justify-between py-1.5">
                  <span className="mono text-[11px] ink-mute uppercase tracking-[0.2em]">Molecules</span>
                  <span className="mono text-[12px] ink">{batch.count}</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span className="mono text-[11px] ink-mute uppercase tracking-[0.2em]">Successful</span>
                  <span className="mono text-[12px] lime">{batch.ok}</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span className="mono text-[11px] ink-mute uppercase tracking-[0.2em]">Failed</span>
                  <span className="mono text-[12px] text-[rgb(255_74_128)]">{batch.failed}</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span className="mono text-[11px] ink-mute uppercase tracking-[0.2em]">Latency</span>
                  <span className="mono text-[12px] ink">{batch.latency_ms} ms</span>
                </div>
                <button onClick={exportCsv} className="btn btn-lime w-full justify-center mt-5">
                  <Download size={14} /> Export results
                </button>
              </>
            ) : (
              <p className="mono text-[12px] ink-dim leading-[1.9]">
                Upload a CSV to see a summary here — molecule count, successes, failures, and total latency.
              </p>
            )}
          </div>
        </div>
      </div>

      {batch && batch.items?.length > 0 && (
        <div className="mt-10 border hairline overflow-x-auto">
          <table className="w-full text-left mono text-[12px]">
            <thead>
              <tr className="bg-soft ink-mute uppercase tracking-[0.2em] text-[10px]">
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">SMILES</th>
                <th className="px-4 py-3">HIA</th>
                <th className="px-4 py-3">BBB</th>
                <th className="px-4 py-3">CYP2D6</th>
                <th className="px-4 py-3">Sol.</th>
                <th className="px-4 py-3">VDss</th>
              </tr>
            </thead>
            <tbody>
              {batch.items.map((it) => (
                <tr key={it.row_idx} className="border-t hairline-soft">
                  <td className="px-4 py-3 ink-mute">{it.row_idx}</td>
                  <td className="px-4 py-3 ink">{it.name || "—"}</td>
                  <td className="px-4 py-3 ink-dim max-w-[220px] truncate" title={it.smiles}>{it.smiles}</td>
                  {it.error ? (
                    <td className="px-4 py-3 text-[rgb(255_74_128)]" colSpan={5}>{it.error}</td>
                  ) : (
                    <>
                      <td className="px-4 py-3 ink">{fmtPct(it.results?.HIA?.probability || 0)}</td>
                      <td className="px-4 py-3 ink">{fmtPct(it.results?.BBB?.probability || 0)}</td>
                      <td className="px-4 py-3 ink">{fmtPct(it.results?.CYP2D6?.probability || 0)}</td>
                      <td className="px-4 py-3 ink">{fmtNum(it.results?.Solubility?.value, 2)}</td>
                      <td className="px-4 py-3 ink">{fmtNum(it.results?.VDss?.value, 2)}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
