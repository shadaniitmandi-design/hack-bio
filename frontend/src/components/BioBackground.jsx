import React, { useEffect, useRef } from "react";

/**
 * BioBackground v2 — a colourful, animated bio backdrop:
 *  • ~18 small floating 3D-looking DNA helices in a rich palette
 *  • drifting molecular network with proximity edges
 *  • glowing pulsing hubs (nucleus / bloom nodes)
 *  • soft binary rain on both edges
 *
 * Everything runs on a single canvas via requestAnimationFrame for smoothness.
 */
export default function BioBackground() {
  const canvasRef = useRef(null);
  const rafRef = useRef(0);
  const stateRef = useRef({
    nodes: [],
    helices: [],
    binary: [],
    hubs: [],
    w: 0,
    h: 0,
    dpr: 1,
    t: 0,
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const S = stateRef.current;
    const rand = (a, b) => a + Math.random() * (b - a);
    const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

    // Vibrant palette (rgb tuples)
    const COLORS = [
      [93, 227, 255],   // cyan
      [74, 232, 200],   // teal
      [152, 128, 255],  // violet
      [255, 108, 195],  // magenta
      [255, 190, 92],   // amber
      [120, 240, 140],  // spring green
      [100, 160, 255],  // sky blue
      [255, 130, 130],  // coral
    ];
    const rgba = (rgb, a) => `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`;

    const resize = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const w = window.innerWidth;
      const h = window.innerHeight;
      S.w = w;
      S.h = h;
      S.dpr = dpr;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      build();
    };

    const build = () => {
      const { w, h } = S;

      // Small floating molecular nodes
      const density = Math.min(140, Math.max(60, Math.floor((w * h) / 22000)));
      S.nodes = new Array(density).fill(0).map(() => {
        const c = pick(COLORS);
        return {
          x: Math.random() * w,
          y: Math.random() * h,
          vx: rand(-0.15, 0.15),
          vy: rand(-0.15, 0.15),
          r: rand(0.6, 1.9),
          c,
          a: rand(0.35, 0.9),
          tw: rand(0, Math.PI * 2),
        };
      });

      // Glowing hubs
      S.hubs = new Array(7).fill(0).map(() => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: rand(-0.05, 0.05),
        vy: rand(-0.04, 0.04),
        r: rand(6, 12),
        c: pick(COLORS),
        phase: rand(0, Math.PI * 2),
      }));

      // Many small 3D-looking DNA helices
      const helixCount = Math.max(14, Math.min(22, Math.floor((w * h) / 90000)));
      S.helices = new Array(helixCount).fill(0).map(() => {
        const cA = pick(COLORS);
        // Sometimes use a two-tone helix (each strand a different colour)
        let cB = cA;
        if (Math.random() < 0.55) {
          do { cB = pick(COLORS); } while (cB === cA);
        }
        return {
          cx: rand(0, w),
          cy: rand(0, h),
          angle: rand(0, Math.PI * 2),
          rotSpeed: rand(-0.25, 0.25),      // rad/sec
          length: rand(90, 190),
          radius: rand(10, 22),
          turns: rand(1.4, 2.8),
          phase: rand(0, Math.PI * 2),
          phaseSpeed: rand(0.7, 1.6),       // helix twist speed
          vx: rand(-0.12, 0.12),
          vy: rand(-0.08, 0.08),
          bobPhase: rand(0, Math.PI * 2),
          bobAmp: rand(2, 8),
          cA,
          cB,
          steps: 22,
          alpha: rand(0.75, 1.0),
        };
      });

      // Binary rain on both edges
      const cols = 4;
      S.binary = [];
      for (let i = 0; i < cols; i++) {
        S.binary.push({ x: 12 + i * 14, y: rand(-h, 0), speed: rand(30, 70), side: "left" });
        S.binary.push({ x: w - 12 - i * 14, y: rand(-h, 0), speed: rand(30, 70), side: "right" });
      }
    };

    // ----- draw helpers -----
    const drawNodes = () => {
      const { w, h, nodes, t } = S;
      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < -5) n.x = w + 5;
        else if (n.x > w + 5) n.x = -5;
        if (n.y < -5) n.y = h + 5;
        else if (n.y > h + 5) n.y = -5;
        const twinkle = 0.6 + Math.sin(t * 0.002 + n.tw) * 0.4;
        ctx.fillStyle = rgba(n.c, (n.a * twinkle).toFixed(3));
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fill();
      }
      const MAX = 130;
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < MAX * MAX) {
            const d = Math.sqrt(d2);
            const alpha = (1 - d / MAX) * 0.14;
            // mix colours: average
            const mr = Math.round((a.c[0] + b.c[0]) / 2);
            const mg = Math.round((a.c[1] + b.c[1]) / 2);
            const mb = Math.round((a.c[2] + b.c[2]) / 2);
            ctx.strokeStyle = `rgba(${mr},${mg},${mb},${alpha.toFixed(3)})`;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
    };

    const drawHubs = () => {
      const { hubs, t, w, h } = S;
      for (const hub of hubs) {
        hub.x += hub.vx;
        hub.y += hub.vy;
        if (hub.x < -20) hub.x = w + 20;
        else if (hub.x > w + 20) hub.x = -20;
        if (hub.y < -20) hub.y = h + 20;
        else if (hub.y > h + 20) hub.y = -20;
        const p = 0.6 + Math.sin(t * 0.0015 + hub.phase) * 0.4;
        const g = ctx.createRadialGradient(hub.x, hub.y, 0, hub.x, hub.y, hub.r * 8);
        g.addColorStop(0, rgba(hub.c, (0.45 * p).toFixed(3)));
        g.addColorStop(0.5, rgba(hub.c, (0.12 * p).toFixed(3)));
        g.addColorStop(1, rgba(hub.c, 0));
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(hub.x, hub.y, hub.r * 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = rgba(hub.c, (0.9 * p).toFixed(3));
        ctx.beginPath();
        ctx.arc(hub.x, hub.y, hub.r * 0.55, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    // Draw a single 3D-looking DNA at (cx,cy), rotated by angle
    const drawOneHelix = (H, tSec) => {
      const { w, h } = S;
      // update motion
      H.cx += H.vx;
      H.cy += H.vy;
      H.angle += H.rotSpeed * (1 / 60);
      const bob = Math.sin(tSec * 1.1 + H.bobPhase) * H.bobAmp;
      const cy = H.cy + bob;
      // wrap around
      const pad = H.length;
      if (H.cx < -pad) H.cx = w + pad;
      else if (H.cx > w + pad) H.cx = -pad;
      if (cy < -pad) H.cy = h + pad;
      else if (cy > h + pad) H.cy = -pad;

      const L = H.length;
      const R = H.radius;
      const turns = H.turns;
      const steps = H.steps;
      const phase = H.phase + tSec * H.phaseSpeed;

      const cosA = Math.cos(H.angle);
      const sinA = Math.sin(H.angle);

      // Precompute strand points
      const A = [], B = [];
      for (let i = 0; i <= steps; i++) {
        const t = i / steps;                        // 0..1
        const lx = (t - 0.5) * L;                   // local x along axis
        const ang = t * turns * Math.PI * 2 + phase;
        const s = Math.sin(ang);
        const cS = Math.cos(ang);                   // used for depth cue
        const ly1 = R * s;
        const ly2 = -R * s;
        // depth 0..1 (front-most on strand A when cos > 0)
        const d1 = 0.5 + 0.5 * cS;
        const d2 = 0.5 - 0.5 * cS;
        // rotate into world
        const x1 = H.cx + lx * cosA - ly1 * sinA;
        const y1 = cy   + lx * sinA + ly1 * cosA;
        const x2 = H.cx + lx * cosA - ly2 * sinA;
        const y2 = cy   + lx * sinA + ly2 * cosA;
        A.push({ x: x1, y: y1, d: d1 });
        B.push({ x: x2, y: y2, d: d2 });
      }

      // Rungs (draw first so they appear behind the strand caps)
      ctx.lineWidth = 1;
      for (let i = 0; i < A.length; i += 1) {
        const a = A[i], b = B[i];
        // Only draw every other rung to avoid clutter
        if (i % 2 !== 0) continue;
        const midD = (a.d + b.d) / 2;                          // 0..1
        const alpha = (0.18 + 0.35 * midD) * H.alpha;
        // gradient between the two strand colours
        const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
        grad.addColorStop(0, rgba(H.cA, alpha * 0.9));
        grad.addColorStop(1, rgba(H.cB, alpha * 0.9));
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }

      // Strand A (with depth-varying width/alpha)
      for (let i = 0; i < A.length - 1; i++) {
        const p = A[i], q = A[i + 1];
        const d = (p.d + q.d) / 2;
        ctx.lineWidth = 0.6 + 1.6 * d;
        ctx.strokeStyle = rgba(H.cA, (0.35 + 0.55 * d) * H.alpha);
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.stroke();
      }

      // Strand B
      for (let i = 0; i < B.length - 1; i++) {
        const p = B[i], q = B[i + 1];
        const d = (p.d + q.d) / 2;
        ctx.lineWidth = 0.6 + 1.6 * d;
        ctx.strokeStyle = rgba(H.cB, (0.35 + 0.55 * d) * H.alpha);
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.stroke();
      }

      // Bead markers on strands
      for (let i = 0; i < A.length; i += 2) {
        const p = A[i];
        ctx.fillStyle = rgba(H.cA, (0.55 + 0.4 * p.d) * H.alpha);
        ctx.beginPath();
        ctx.arc(p.x, p.y, 0.9 + 1.4 * p.d, 0, Math.PI * 2);
        ctx.fill();
      }
      for (let i = 0; i < B.length; i += 2) {
        const q = B[i];
        ctx.fillStyle = rgba(H.cB, (0.55 + 0.4 * q.d) * H.alpha);
        ctx.beginPath();
        ctx.arc(q.x, q.y, 0.9 + 1.4 * q.d, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    const drawHelices = (tSec) => {
      // sort by y so lower helices render on top (fake depth)
      const list = S.helices.slice().sort((a, b) => a.cy - b.cy);
      for (const H of list) drawOneHelix(H, tSec);
    };

    const drawBinary = (dt) => {
      const { binary, h } = S;
      ctx.font = "11px 'JetBrains Mono', monospace";
      ctx.textBaseline = "top";
      for (const b of binary) {
        b.y += b.speed * dt;
        if (b.y > h + 40) b.y = -40 - Math.random() * 60;
        for (let k = 0; k < 22; k++) {
          const y = b.y + k * 14;
          if (y < -14 || y > h + 14) continue;
          const alpha = 0.12 + (Math.sin((y + b.x) * 0.05) + 1) * 0.05;
          const digit =
            ((Math.floor((y + b.x * 3.7 + S.t * 0.02) / 14) & 1) === 1) ? "1" : "0";
          ctx.fillStyle = `rgba(93,227,255,${alpha.toFixed(3)})`;
          ctx.fillText(digit, b.x, y);
        }
      }
    };

    let last = performance.now();
    const loop = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      S.t = now;
      const tSec = now / 1000;

      ctx.clearRect(0, 0, S.w, S.h);

      // Draw order: helices in back, network dots, hubs bloom, binary rain
      drawHelices(tSec);
      drawNodes();
      drawHubs();
      drawBinary(dt);

      rafRef.current = requestAnimationFrame(loop);
    };

    resize();
    window.addEventListener("resize", resize);
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0, opacity: 0.95 }}
      aria-hidden="true"
    />
  );
}
