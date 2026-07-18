import React, { useEffect, useRef } from "react";

/**
 * BioBackground — dynamic canvas layer inspired by bio-hackathon aesthetics.
 *
 * Renders four synchronised layers:
 *   1. Drifting molecular network (nodes + proximity edges)
 *   2. Multiple horizontally-scrolling DNA double helices
 *   3. Vertical binary streams near the edges
 *   4. Occasional pulsing "hero" nodes with glow
 *
 * Everything runs on a single canvas via requestAnimationFrame.
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

    const PALETTE = [
      "rgba(93, 227, 255,",   // cyan
      "rgba(74, 232, 200,",   // teal
      "rgba(152, 128, 255,",  // violet
      "rgba(255, 190, 92,",   // amber
    ];

    const build = () => {
      const { w, h } = S;
      // Node density scales with viewport area
      const density = Math.min(140, Math.max(60, Math.floor((w * h) / 22000)));
      S.nodes = new Array(density).fill(0).map(() => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: rand(-0.15, 0.15),
        vy: rand(-0.15, 0.15),
        r: rand(0.6, 1.8),
        c: PALETTE[Math.floor(Math.random() * PALETTE.length)],
        a: rand(0.35, 0.9),
        tw: rand(0, Math.PI * 2), // twinkle phase
      }));

      // Featured pulsing hubs (bigger glowing nodes)
      S.hubs = new Array(6).fill(0).map(() => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: rand(-0.05, 0.05),
        vy: rand(-0.04, 0.04),
        r: rand(6, 12),
        c: PALETTE[Math.floor(Math.random() * PALETTE.length)],
        phase: rand(0, Math.PI * 2),
      }));

      // Helices: 3 diagonal double-helix bands
      S.helices = [
        { y: h * 0.22, amp: 42, freq: 0.008, speed: 0.35, tilt: -0.18, hue: "rgba(93,227,255," },
        { y: h * 0.58, amp: 56, freq: 0.006, speed: -0.28, tilt: 0.14, hue: "rgba(74,232,200," },
        { y: h * 0.85, amp: 48, freq: 0.007, speed: 0.24, tilt: -0.1, hue: "rgba(152,128,255," },
      ];

      // Binary streams on both sides
      const cols = 4;
      S.binary = [];
      for (let i = 0; i < cols; i++) {
        // left
        S.binary.push({
          x: 12 + i * 14,
          y: rand(-h, 0),
          speed: rand(30, 70),
          side: "left",
        });
        // right
        S.binary.push({
          x: w - 12 - i * 14,
          y: rand(-h, 0),
          speed: rand(30, 70),
          side: "right",
        });
      }
    };

    const drawNodes = () => {
      const { w, h, nodes, t } = S;
      // update + draw nodes
      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        // wrap
        if (n.x < -5) n.x = w + 5;
        else if (n.x > w + 5) n.x = -5;
        if (n.y < -5) n.y = h + 5;
        else if (n.y > h + 5) n.y = -5;
        const twinkle = 0.6 + Math.sin(t * 0.002 + n.tw) * 0.4;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.c + (n.a * twinkle).toFixed(3) + ")";
        ctx.fill();
      }
      // edges between close nodes
      const MAX_DIST = 130;
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < MAX_DIST * MAX_DIST) {
            const d = Math.sqrt(d2);
            const alpha = (1 - d / MAX_DIST) * 0.18;
            ctx.strokeStyle = `rgba(93,227,255,${alpha.toFixed(3)})`;
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
        g.addColorStop(0, hub.c + (0.45 * p).toFixed(3) + ")");
        g.addColorStop(0.5, hub.c + (0.12 * p).toFixed(3) + ")");
        g.addColorStop(1, hub.c + "0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(hub.x, hub.y, hub.r * 8, 0, Math.PI * 2);
        ctx.fill();
        // core
        ctx.fillStyle = hub.c + (0.9 * p).toFixed(3) + ")";
        ctx.beginPath();
        ctx.arc(hub.x, hub.y, hub.r * 0.55, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    const drawHelices = () => {
      const { helices, w, t } = S;
      for (const H of helices) {
        const phase = t * 0.001 * H.speed;
        const strandA = [];
        const strandB = [];
        const step = 12;
        for (let x = -40; x <= w + 40; x += step) {
          const angle = x * H.freq + phase;
          const yBase = H.y + Math.tan(H.tilt) * (x - w / 2) * 0.15;
          const dy = Math.sin(angle) * H.amp;
          strandA.push({ x, y: yBase + dy });
          strandB.push({ x, y: yBase - dy });
        }
        // rungs between strands (dashed subtle)
        for (let i = 0; i < strandA.length; i += 2) {
          const a = strandA[i];
          const b = strandB[i];
          const glow = 0.10 + 0.10 * Math.sin(t * 0.003 + i * 0.4);
          ctx.strokeStyle = H.hue + glow.toFixed(3) + ")";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
        // strands with soft glow
        const drawStrand = (pts, glowAlpha) => {
          ctx.lineWidth = 1.4;
          ctx.strokeStyle = H.hue + glowAlpha + ")";
          ctx.beginPath();
          pts.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
          ctx.stroke();
        };
        drawStrand(strandA, "0.55");
        drawStrand(strandB, "0.35");
        // dot markers on strands
        for (let i = 0; i < strandA.length; i += 3) {
          const p = strandA[i];
          const q = strandB[i];
          ctx.fillStyle = H.hue + "0.75)";
          ctx.beginPath();
          ctx.arc(p.x, p.y, 1.6, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = H.hue + "0.45)";
          ctx.beginPath();
          ctx.arc(q.x, q.y, 1.4, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    };

    const drawBinary = (dt) => {
      const { binary, h } = S;
      ctx.font = "11px 'JetBrains Mono', monospace";
      ctx.textBaseline = "top";
      for (const b of binary) {
        b.y += b.speed * dt;
        if (b.y > h + 40) b.y = -40 - Math.random() * 60;
        // Draw a column of 0/1 characters
        for (let k = 0; k < 22; k++) {
          const y = b.y + k * 14;
          if (y < -14 || y > h + 14) continue;
          const alpha = 0.14 + (Math.sin((y + b.x) * 0.05) + 1) * 0.05;
          // Use a deterministic-ish digit per position/time slice
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

      // clear
      ctx.clearRect(0, 0, S.w, S.h);

      // subtle background wash
      const grad = ctx.createLinearGradient(0, 0, S.w, S.h);
      grad.addColorStop(0, "rgba(6,12,34,0)");
      grad.addColorStop(1, "rgba(4,8,24,0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, S.w, S.h);

      drawHelices();
      drawHubs();
      drawNodes();
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
      style={{ zIndex: 0, opacity: 0.85 }}
      aria-hidden="true"
    />
  );
}
