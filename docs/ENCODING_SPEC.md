# Encoding specification

`latin-a1z26-v1`: NFC normalization, ASCII lowercase-to-uppercase, then retain A–Z. With `letters_only=true` (default), ASCII whitespace and `. , ' ! ? -` are removed and reported. Other characters are rejected; no transliteration or silent accent folding. Each letter is a two-digit token from `01` through `26`. `ADA` → `010401`; `PI` → `1609`.

`utf8-decimal-v1`: NFC normalization, UTF-8 bytes, each as a three-digit decimal token. `PI` → `080073`. It accepts Unicode text except controls and invalid surrogate sequences. The normalized text can differ from the raw input, and both are returned.

Raw text is limited to 128 Unicode code points; encoded patterns to 384 digits. Leading zeros are significant. The encoding result includes the raw text, normalized text, removed units, token mapping, profile ID/version, and exact pattern. The backend is authoritative; the frontend asks `/api/encode` for previews rather than recreating the algorithm.
