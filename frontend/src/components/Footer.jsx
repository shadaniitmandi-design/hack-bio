import React from "react";

export default function Footer() {
  return (
    <footer className="relative z-10 border-t hairline mt-24">
      <div className="max-w-[1400px] mx-auto px-8 py-8 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        <div className="mono text-[11px] ink-mute uppercase tracking-[0.2em]">
          © 2026 · HelixADMET Labs
        </div>
        <div className="mono text-[11px] ink-mute uppercase tracking-[0.2em] text-center">
          Trained on TDC · MoleculeNet · ChEMBL
        </div>
        <div className="mono text-[11px] ink-mute uppercase tracking-[0.2em] md:text-right">
          Build 04 · Fingerprint x XGBoost
        </div>
      </div>
    </footer>
  );
}
