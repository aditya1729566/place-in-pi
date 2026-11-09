import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = { title: "Pi Dictionary — Find a pattern in π", description: "Encode text transparently, search a verified prefix of π, and inspect every exact match." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>
    <header className="site-header"><div className="header-inner">
      <Link href="/" className="brand" aria-label="Pi Dictionary home"><span className="brand-mark">π</span><span>PI DICTIONARY</span></Link>
      <nav aria-label="Main navigation"><Link href="/search">Search</Link><Link href="/explore">Explore</Link><Link href="/encodings">Encodings</Link><Link href="/about">About</Link></nav>
    </div></header>
    <main>{children}</main>
    <footer className="site-footer"><div className="footer-inner"><span>PI DICTIONARY <span className="muted">/ exact patterns, visible evidence</span></span><span><Link href="/methodology">Methodology</Link> · <Link href="/about">About</Link></span></div></footer>
  </body></html>;
}
