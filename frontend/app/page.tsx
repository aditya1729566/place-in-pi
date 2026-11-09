import Link from "next/link";
import SearchExperience from "@/components/SearchExperience";

export default function Home() {
  return <>
    <section className="hero wrap">
      <div className="hero-copy"><p className="eyebrow">A FIELD GUIDE TO π</p><h1>Every pattern<br />has a <em>position.</em></h1><p className="lede">Turn a word into digits. Search a verified prefix of π. See the exact place it appears—or the limit of what we searched.</p><SearchExperience compact /><p className="hero-note">Your search stays in this session. The encoding is always shown before the result.</p></div>
      <div className="hero-art" aria-hidden="true"><div className="orbit orbit-a"/><div className="orbit orbit-b"/><div className="hero-art-label">DECIMAL FIELD <span>01—∞</span></div><div className="hero-pi">π</div><div className="hero-digits">1415926535897932384626433832795028841971693993751058209749445923078164</div><div className="hero-coordinate">POSITION 000001 <span>→</span> 1415926535</div></div>
    </section>
    <section className="home-steps wrap"><div><p className="eyebrow">01 / ENCODE</p><h2>Show the rule.</h2><p>Each letter or byte becomes a fixed-width decimal token. Compare profiles without hidden transformations.</p><Link href="/encodings" className="text-link">See encodings ↗</Link></div><div><p className="eyebrow">02 / LOCATE</p><h2>Read the evidence.</h2><p>Matches come from a verified finite corpus. Every result includes the exact pattern, position, and searched range.</p><Link href="/search" className="text-link">Search π ↗</Link></div><div><p className="eyebrow">03 / EXPLORE</p><h2>Follow the digits.</h2><p>Jump to a match and move through the sequence in Grid, Spiral, or Line view.</p><Link href="/explore" className="text-link">Open observatory ↗</Link></div></section>
  </>;
}
