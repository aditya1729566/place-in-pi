"use client";

import { FormEvent, PointerEvent, WheelEvent, useEffect, useRef, useState } from "react";
import { api, number, type Corpus } from "@/lib/api";

type Layout = "grid" | "spiral" | "line";
type Display = "numbers" | "blocks" | "braille";
type Hit = { x: number; y: number; position: number };
const colors = ["#547ea6", "#bd6d65", "#b88e44", "#568b83", "#807cbb", "#b85d83", "#4c9caa", "#a47755", "#82994f", "#a96898"];
// Standard literary Braille digit cells, shown individually without a number sign.
const braille = ["⠚", "⠁", "⠃", "⠉", "⠙", "⠑", "⠋", "⠛", "⠓", "⠊"];

function points(layout: Layout, count: number, width: number, height: number, cell: number): { x: number; y: number }[] {
  const result = [];
  if (layout === "grid") {
    const columns = Math.max(1, Math.floor(width / cell));
    for (let i = 0; i < count; i++) result.push({ x: (i % columns) * cell + cell / 2, y: Math.floor(i / columns) * cell + cell / 2 });
  } else if (layout === "line") {
    for (let i = 0; i < count; i++) result.push({ x: i * cell + cell / 2, y: height / 2 });
  } else {
    let x = 0, y = 0, dx = 1, dy = 0, leg = 1, walked = 0, turns = 0;
    for (let i = 0; i < count; i++) {
      result.push({ x: width / 2 + x * cell, y: height / 2 + y * cell });
      x += dx; y += dy; walked++;
      if (walked === leg) { walked = 0; [dx, dy] = [-dy, dx]; turns++; if (turns % 2 === 0) leg++; }
    }
  }
  return result;
}

export default function Visualizer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hits = useRef<Hit[]>([]);
  const down = useRef<{ x: number; y: number } | null>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 500 });
  const [corpus, setCorpus] = useState<Corpus | null>(null);
  const [error, setError] = useState("");
  const [position, setPosition] = useState(1);
  const [jump, setJump] = useState("1");
  const [matchStart, setMatchStart] = useState(0);
  const [matchLength, setMatchLength] = useState(0);
  const [layout, setLayout] = useState<Layout>("grid");
  const [display, setDisplay] = useState<Display>("numbers");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [zoom, setZoom] = useState(1);
  const [windowData, setWindowData] = useState<{ start: number; digits: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const cell = Math.round(39 * zoom);
  const columns = Math.max(1, Math.floor(dimensions.width / cell));
  const rows = Math.max(1, Math.floor(dimensions.height / cell));
  const visibleCount = layout === "grid" ? columns * rows : layout === "line" ? columns : Math.min(1000, Math.max(1, Math.floor(Math.min(columns, rows) ** 2 / 1.8)));
  const start = layout === "spiral" ? position : Math.max(1, position - Math.floor(visibleCount / 2));
  const count = corpus ? Math.max(0, Math.min(visibleCount, 4096, corpus.digits - start + 1)) : 0;

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initial = Number(params.get("position") || 1);
    const length = Number(params.get("length") || 0);
    if (Number.isSafeInteger(initial) && initial > 0) { setPosition(initial); setJump(String(initial)); }
    if (Number.isSafeInteger(length) && length > 0 && length <= 384) { setMatchStart(initial); setMatchLength(length); }
    const stored = localStorage.getItem("pi-theme");
    if (stored === "dark") setTheme("dark");
    api<Corpus>("/api/corpus").then(setCorpus).catch(err => { setError(err.message); setLoading(false); });
  }, []);

  useEffect(() => { if (corpus && position > corpus.digits) { setPosition(corpus.digits); setJump(String(corpus.digits)); } }, [corpus, position]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const observer = new ResizeObserver(entries => {
      const rect = entries[0].contentRect;
      setDimensions({ width: Math.max(200, rect.width), height: Math.max(260, rect.height) });
    });
    observer.observe(canvas);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!corpus || !count) return;
    let active = true;
    const timer = setTimeout(() => {
      setLoading(true);
      api<{ start: number; digits: string }>(`/api/digits?start=${start}&count=${count}`)
        .then(data => { if (active) { setWindowData(data); setError(""); } })
        .catch(err => { if (active) setError(err.message); })
        .finally(() => { if (active) setLoading(false); });
    }, 65);
    return () => { active = false; clearTimeout(timer); };
  }, [corpus, start, count]);

  useEffect(() => { if (corpus && position > corpus.digits) { setPosition(corpus.digits); setJump(String(corpus.digits)); } }, [corpus, position]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !windowData) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.floor(dimensions.width * ratio);
    canvas.height = Math.floor(dimensions.height * ratio);
    const context = canvas.getContext("2d");
    if (!context) return;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.fillStyle = theme === "dark" ? "#102630" : "#eaf1ee";
    context.fillRect(0, 0, dimensions.width, dimensions.height);
    const coords = points(layout, windowData.digits.length, dimensions.width, dimensions.height, cell);
    const nextHits: Hit[] = [];
    for (let i = 0; i < windowData.digits.length; i++) {
      const { x, y } = coords[i];
      if (x < -cell || y < -cell || x > dimensions.width + cell || y > dimensions.height + cell) continue;
      const digit = Number(windowData.digits[i]);
      const absolute = windowData.start + i;
      const selected = absolute === position;
      const matching = matchStart > 0 && absolute >= matchStart && absolute < matchStart + matchLength;
      const width = cell * (layout === "line" ? 0.86 : 0.88);
      const height = cell * 0.88;
      context.fillStyle = display === "blocks" ? colors[digit] : theme === "dark" ? "#1b3b49" : "#ffffff";
      context.fillRect(x - width / 2, y - height / 2, width, height);
      if (display !== "blocks") {
        context.fillStyle = theme === "dark" ? "#eaf3ee" : "#183442";
        context.font = `${Math.round(cell * (display === "braille" ? 0.62 : 0.47))}px ${display === "braille" ? "sans-serif" : "monospace"}`;
        context.textAlign = "center"; context.textBaseline = "middle";
        context.fillText(display === "braille" ? braille[digit] : String(digit), x, y + 1);
      }
      if (matching || selected) {
        context.lineWidth = selected ? 3 : 2;
        context.strokeStyle = selected ? "#cf694f" : "#7774ad";
        context.strokeRect(x - width / 2 + 1, y - height / 2 + 1, width - 2, height - 2);
      }
      nextHits.push({ x, y, position: absolute });
    }
    hits.current = nextHits;
  }, [windowData, dimensions, layout, display, theme, cell, position, matchStart, matchLength]);

  function move(delta: number) { if (corpus) { const next = Math.max(1, Math.min(corpus.digits, position + delta)); setPosition(next); setJump(String(next)); } }
  function changeTheme(value: "light" | "dark") { setTheme(value); localStorage.setItem("pi-theme", value); }
  function onWheel(event: WheelEvent<HTMLCanvasElement>) { event.preventDefault(); setZoom(current => Math.max(0.65, Math.min(2.5, current + (event.deltaY < 0 ? 0.12 : -0.12)))); }
  function onPointerDown(event: PointerEvent<HTMLCanvasElement>) { down.current = { x: event.clientX, y: event.clientY }; event.currentTarget.setPointerCapture(event.pointerId); }
  function onPointerUp(event: PointerEvent<HTMLCanvasElement>) {
    if (!down.current) return;
    const dx = event.clientX - down.current.x, dy = event.clientY - down.current.y;
    if (Math.hypot(dx, dy) > 8) move(layout === "grid" ? Math.round((-dy / cell) * columns - dx / cell) : Math.round(-dx / cell - dy / cell));
    else {
      const rect = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - rect.left, y = event.clientY - rect.top;
      const hit = hits.current.reduce<Hit | null>((best, current) => !best || Math.hypot(current.x - x, current.y - y) < Math.hypot(best.x - x, best.y - y) ? current : best, null);
      if (hit && Math.hypot(hit.x - x, hit.y - y) < cell * 0.7) { setPosition(hit.position); setJump(String(hit.position)); }
    }
    down.current = null;
  }
  function onKey(event: React.KeyboardEvent) { if (event.key === "ArrowLeft") { event.preventDefault(); move(-1); } if (event.key === "ArrowRight") { event.preventDefault(); move(1); } if (event.key === "ArrowUp") { event.preventDefault(); move(-columns); } if (event.key === "ArrowDown") { event.preventDefault(); move(columns); } }
  function onJump(event: FormEvent) { event.preventDefault(); const value = Number(jump); if (corpus && Number.isSafeInteger(value) && value >= 1 && value <= corpus.digits) { setPosition(value); setError(""); } else setError(`Choose a position from 1 to ${number(corpus?.digits || 0)}.`); }
  const selectedIndex = windowData ? position - windowData.start : -1;
  const context = windowData && selectedIndex >= 0 && selectedIndex < windowData.digits.length ? windowData.digits.slice(Math.max(0, selectedIndex - 12), Math.min(windowData.digits.length, selectedIndex + 13)) : "";

  return <div className={`visualizer ${theme}`}>
    <div className="visualizer-toolbar"><div className="control-group" aria-label="Layout"><span>LAYOUT</span>{(["grid", "spiral", "line"] as Layout[]).map(value => <button key={value} aria-pressed={layout === value} onClick={() => setLayout(value)}>{value}</button>)}</div><div className="control-group" aria-label="Display"><span>DISPLAY</span>{(["numbers", "blocks", "braille"] as Display[]).map(value => <button key={value} aria-pressed={display === value} onClick={() => setDisplay(value)}>{value === "blocks" ? "Color blocks" : value}</button>)}</div><div className="control-group" aria-label="Theme"><span>THEME</span>{(["light", "dark"] as const).map(value => <button key={value} aria-pressed={theme === value} onClick={() => changeTheme(value)}>{value}</button>)}</div></div>
    <div className="visualizer-body"><div className="canvas-area"><canvas ref={canvasRef} className="digit-canvas" tabIndex={0} aria-label={`${layout} visualization of verified pi digits; use arrow keys to move`} onKeyDown={onKey} onWheel={onWheel} onPointerDown={onPointerDown} onPointerUp={onPointerUp} onPointerCancel={() => { down.current = null; }} />{loading && <div className="canvas-loading" role="status">Loading verified digits…</div>}{error && <div className="canvas-error" role="alert">{error}</div>}</div><aside className="visualizer-side"><p className="eyebrow">CURRENT COORDINATE</p><strong className="current-position">#{number(position)}</strong><span>of {corpus ? number(corpus.digits) : "—"} verified digits</span><form onSubmit={onJump} className="jump-form"><label htmlFor="jump-position">Jump to digit</label><div><input id="jump-position" type="number" min="1" max={corpus?.digits} value={jump} onChange={event => setJump(event.target.value)} /><button>Go</button></div></form><div className="zoom-controls"><span>Zoom {zoom.toFixed(1)}×</span><button onClick={() => setZoom(value => Math.max(0.65, value - 0.2))} aria-label="Zoom out">−</button><button onClick={() => setZoom(value => Math.min(2.5, value + 0.2))} aria-label="Zoom in">+</button></div><div className="pan-controls"><button onClick={() => move(-Math.max(1, columns))}>← Earlier</button><button onClick={() => move(Math.max(1, columns))}>Later →</button></div><button className="copy-link" onClick={() => navigator.clipboard.writeText(`${location.origin}/explore?position=${position}${matchLength ? `&length=${matchLength}` : ""}`)}>Copy position link ↗</button><p className="canvas-help">Drag to pan, scroll to zoom, or use arrow keys while the digit field is focused.</p></aside></div>
    <div className="visualizer-bottom"><div tabIndex={0} className="accessible-context" onKeyDown={onKey}><span className="eyebrow">DIGIT CONTEXT</span><code>{context || "Select a digit to read its neighbors."}</code><span className="sr-only">Selected digit position {position}. {context && `Nearby digits: ${context}`}</span></div><div className="digit-legend" aria-label="Digit color legend">{colors.map((color, digit) => <span key={digit}><i style={{ background: color }} />{digit}</span>)}</div>{display === "braille" && <p className="braille-note">Braille uses standard number cells for individual digits, without a number sign; the context line shows the original decimal digits.</p>}</div>
  </div>;
}
