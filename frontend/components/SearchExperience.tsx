"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, post, number, type Corpus, type Encoding, type SearchResponse } from "@/lib/api";

const LATIN = "latin-a1z26-v1";
const UTF8 = "utf8-decimal-v1";

function Probability({ digits, length }: { digits: number; length: number }) {
  const starts = Math.max(0, digits - length + 1);
  const expected = starts * Math.pow(10, -length);
  const chance = -Math.expm1(-expected);
  const label = chance < 0.000001 ? "below 0.0001%" : `${(chance * 100).toPrecision(3)}%`;
  return <div className="model-note"><strong>Model estimate</strong><span>Chance of at least one in this range: {label}</span><small>Independent uniform-digit approximation; π is not proved normal. This estimate is separate from the measured result.</small></div>;
}

function Occurrences({ response }: { response: SearchResponse }) {
  const [contexts, setContexts] = useState<Record<number, string>>({});
  const positions = response.result.matches;
  const length = response.query.pattern_length;
  useEffect(() => {
    let active = true;
    setContexts({});
    Promise.all(positions.map(async position => {
      const start = Math.max(1, position - 8);
      const count = Math.min(length + 16, response.corpus.digits_searched - start + 1);
      const data = await api<{ digits: string }>(`/api/digits?start=${start}&count=${count}`);
      const before = data.digits.slice(0, position - start);
      const match = data.digits.slice(position - start, position - start + length);
      const after = data.digits.slice(position - start + length);
      return [position, `${before}|${match}|${after}`] as const;
    })).then(rows => { if (active) setContexts(Object.fromEntries(rows)); }).catch(() => {});
    return () => { active = false; };
  }, [response]);
  if (!positions.length) return null;
  return <ol className="occurrence-list">{positions.map(position => {
    const parts = contexts[position]?.split("|");
    return <li key={position}><div><span className="position-label">DIGIT #{number(position)}</span><span className="context-digits">{parts ? <>{parts[0]}<mark>{parts[1]}</mark>{parts[2]}</> : "Loading context…"}</span></div><Link className="jump-link" href={`/explore?position=${position}&length=${length}`}>Explore ↗</Link></li>;
  })}</ol>;
}

export default function SearchExperience({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [profile, setProfile] = useState(LATIN);
  const [preview, setPreview] = useState<Encoding | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [corpus, setCorpus] = useState<Corpus | null>(null);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [comparison, setComparison] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    api<Corpus>("/api/corpus").then(setCorpus).catch(() => setCorpus(null));
    if (!compact) {
      const pending = sessionStorage.getItem("pi-pending-query");
      sessionStorage.removeItem("pi-pending-query");
      let parsed: { text: string; profile: string } | null = null;
      try { parsed = pending ? JSON.parse(pending) as { text: string; profile: string } : null; } catch { parsed = null; }
      const initial = parsed?.text || "";
      const selected = parsed?.profile === UTF8 ? UTF8 : LATIN;
      if (initial) {
        setText(initial); setProfile(selected);
        setLoading(true);
        post<SearchResponse>("/api/search", { text: initial, profile_id: selected })
          .then(setResult).catch(err => setError(err.message)).finally(() => setLoading(false));
      }
    }
  }, [compact]);

  useEffect(() => {
    if (!text.trim()) { setPreview(null); setPreviewError(""); return; }
    let active = true;
    const timer = setTimeout(() => {
      post<Encoding>("/api/encode", { text, profile_id: profile }).then(data => {
        if (active) { setPreview(data); setPreviewError(""); }
      }).catch(err => { if (active) { setPreview(null); setPreviewError(err.message); } });
    }, 180);
    return () => { active = false; clearTimeout(timer); };
  }, [text, profile]);

  async function run(cursor?: string) {
    setError(""); setLoading(true);
    if (!cursor) { setResult(null); setComparison(null); }
    try {
      const response = await post<SearchResponse>("/api/search", { text, profile_id: profile, cursor, limit: 20 });
      setResult(response);
    } catch (err) { setError(err instanceof Error ? err.message : "Search failed."); }
    finally { setLoading(false); }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!text.trim() || previewError) return;
    if (compact) { sessionStorage.setItem("pi-pending-query", JSON.stringify({ text, profile })); router.push("/search"); }
    else void run();
  }

  async function compare() {
    if (!result) return;
    const other = profile === LATIN ? UTF8 : LATIN;
    setComparing(true);
    try { setComparison(await post<SearchResponse>("/api/search", { text, profile_id: other, limit: 1 })); }
    catch (err) { setError(err instanceof Error ? err.message : "Comparison failed."); }
    finally { setComparing(false); }
  }

  return <div className={compact ? "search-experience compact" : "search-experience"}>
    <form onSubmit={submit} className="search-form"><label htmlFor={compact ? "home-query" : "search-query"}>Name, word, or phrase</label><div className="search-line"><input id={compact ? "home-query" : "search-query"} value={text} onChange={e => { setText(e.target.value); if (!compact) { setResult(null); setComparison(null); } }} placeholder="Try your name, or PI" maxLength={128} autoComplete="off" /><button className="button" disabled={!text.trim() || !!previewError || loading}>{loading ? "Searching…" : "Find in π"}<span aria-hidden="true">↗</span></button></div>
      <div className="search-options"><label htmlFor={compact ? "home-profile" : "search-profile"}>Encoding</label><select id={compact ? "home-profile" : "search-profile"} value={profile} onChange={e => { setProfile(e.target.value); if (!compact) { setResult(null); setComparison(null); } }}><option value={LATIN}>Latin A1Z26</option><option value={UTF8}>Unicode UTF-8 bytes</option></select><span className="muted">Exact decimal matching</span></div>
    </form>
    {previewError && <p className="form-error" role="alert">{previewError} {profile === LATIN && <button className="inline-button" onClick={() => setProfile(UTF8)}>Use Unicode encoding</button>}</p>}
    {preview && <div className="encoding-preview"><div className="panel-head"><span className="eyebrow">ENCODING INSPECTOR</span><span>{preview.pattern_length} digits · v{preview.profile_version}</span></div><p className="conversion-path"><span>{preview.raw_text}</span><span aria-hidden="true">→</span><span>{preview.normalized_text}</span><span aria-hidden="true">→</span><strong>{preview.encoded_pattern}</strong><button className="copy-button" onClick={() => navigator.clipboard.writeText(preview.encoded_pattern)} aria-label="Copy decimal pattern">Copy</button></p><div className="unit-list">{preview.units.slice(0, 32).map((unit, index) => <span key={index}>{unit.normalized_unit} <b>{unit.token}</b></span>)}{preview.units.length > 32 && <span>+{preview.units.length - 32} more units</span>}</div>{preview.removed_units.length > 0 && <small>Removed by letters-only rule: {preview.removed_units.map(char => char === " " ? "space" : char).join(", ")}</small>}</div>}
    <p className="coverage-line">{corpus ? <>Verified local coverage <strong>{number(corpus.digits)} decimal digits</strong> <span>· {corpus.version}</span></> : "Corpus unavailable. Start the API and import a verified dataset."}</p>
    {!compact && <div className="result-zone" aria-live="polite">{error && <div className="notice error" role="alert">{error}</div>}{loading && <div className="notice">Searching the verified digits…</div>}{result && <>
      <div className="result-summary"><div><p className="eyebrow">EXACT SEARCH / {result.execution.method.toUpperCase()}</p><h2>{result.result.found ? <>First match at digit <span>#{number(result.result.first_position!)}</span></> : "No match in the searched prefix."}</h2><p>{result.result.found ? `${result.result.total_matches === null ? "Count incomplete" : `${number(result.result.total_matches)} total overlapping occurrence${result.result.total_matches === 1 ? "" : "s"}`}.` : `No occurrence found in the first ${number(result.corpus.digits_searched)} verified decimal digits.`} {result.execution.complete ? `Search completed in ${result.execution.elapsed_ms} ms.` : "Search timed out; the count is incomplete."}</p></div><div className="result-stamp">{number(result.corpus.digits_searched)}<span>DIGITS SEARCHED</span></div></div>
      {result.result.found && <><div className="section-heading"><h3>Occurrences</h3><span>{result.result.matches.length} positions on this page</span></div><Occurrences response={result} />{result.result.next_cursor && <button className="secondary-button" onClick={() => run(result.result.next_cursor!)} disabled={loading}>Next positions →</button>}</>}
      <div className="result-bottom"><button className="secondary-button" onClick={compare} disabled={comparing}>{comparing ? "Comparing…" : "Compare other encoding"}</button><Probability digits={result.corpus.digits_searched} length={result.query.pattern_length} /></div>
      {comparison && <div className="comparison"><p className="eyebrow">OTHER PROFILE / {comparison.query.profile_id}</p><strong>{comparison.query.encoded_pattern}</strong><span>{comparison.result.found ? `First match: #${number(comparison.result.first_position!)}` : `Not found in the first ${number(comparison.corpus.digits_searched)} digits`}</span></div>}
    </>}</div>}
  </div>;
}
