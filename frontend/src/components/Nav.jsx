import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-3 group">
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 4L28 28M28 4L4 28" stroke="rgb(93 227 255)" strokeWidth="1.6" />
        <circle cx="16" cy="16" r="3.2" stroke="rgb(93 227 255)" strokeWidth="1.6" fill="none" />
        <circle cx="4" cy="16" r="1.6" fill="rgb(93 227 255)" />
        <circle cx="28" cy="16" r="1.6" fill="rgb(93 227 255)" />
        <circle cx="16" cy="4" r="1.6" fill="rgb(93 227 255)" />
        <circle cx="16" cy="28" r="1.6" fill="rgb(93 227 255)" />
      </svg>
      <div className="display font-bold tracking-tight text-[18px] leading-none">
        <span className="ink">HELIX</span>
        <span className="lime">ADMET</span>
      </div>
    </Link>
  );
}

export default function Nav() {
  const loc = useLocation();
  const nav = useNavigate();
  const isActive = (p) => loc.pathname === p;
  return (
    <header className="relative z-20 border-b hairline">
      <div className="max-w-[1400px] mx-auto px-8 h-[72px] flex items-center justify-between">
        <Logo />
        <nav className="hidden md:flex items-center gap-10">
          <Link to="/predict" className="nav-link" data-active={isActive("/predict")}>Predict</Link>
          <Link to="/pipeline" className="nav-link" data-active={isActive("/pipeline")}>Pipeline</Link>
        </nav>
        <button onClick={() => nav("/predict")} className="btn btn-ghost">
          Launch Console
        </button>
      </div>
    </header>
  );
}
