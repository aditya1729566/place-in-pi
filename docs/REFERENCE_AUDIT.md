# Reference audit — Place in Pi

Inspected 2026-11-09 at https://placeinpi.com/. The installed `rea@rea` plugin was not connected to this chat, so no REA Evidence ID or runtime capture is claimed. The available reverse-engineering skill's browser fallback was used: live browser accessibility trees, screenshots, and declared UI actions. Desktop was observed in Safari at approximately 2940×1680; mobile was observed in the in-app browser at approximately 587×729. These are observations of the rendered site, not an audit of its source or data integrity.

## Observed

- The canvas occupies nearly the whole viewport, with a floating top search/navigation bar and small digit/zoom readout at the bottom. Desktop shows search, encoding choices, Famous, achievements, and shop in the header. Mobile shows a five-item bottom nav and puts constant and settings choices in a drawer.
- A mobile search for `PI` returned a mapping `P = 15`, `I = 08`, pattern `1508`, a count, previous/next match controls, a probability overlay, and a highlighted viewport jump. This mapping differs from our specified A1Z26 (`PI` → `1609`). The result count was observed in the site UI only; it was not independently verified.
- Settings offered Numbers, Color Blocks, Braille; Grid, Spiral, Line; and Dark, Light. Switching Color Blocks visibly replaced digits with colored cells. The selected layout and display were exposed as radio controls.
- Famous opened a mobile sheet listing sequences and positions, including the Feynman point. A desktop result showed a multi-profile comparison, position ruler, highlighted context, and a canvas overview. A pre-existing query was present in that desktop tab; its numerical claims were not independently checked.
- The mobile loading screen says “Loading digits...” and then reveals the visualization. A mascot gives prompts and search feedback. The shop and checkout are excluded from our product.

## Strengths and gaps for our design

The immediate spatial jump from a found sequence to the digits is useful; preserve that interaction. The full-viewport canvas makes controls and result evidence harder to scan, especially on mobile, and the observed color visualization has no persistent numeric legend. Our design uses a legible search/result column and a separate digit observatory, with visible encoding, corpus boundary, count status, and a color legend. It will not reuse the site's graphics, copy, mascot, branding, or shop.

## Remaining evidence boundary

REA scenario capture and desktop viewport performance tracing were unavailable in this chat because the plugin did not expose its tools. Browser QA of our implementation will establish our own behavior, but cannot prove any unobserved reference behavior.

## Our implementation QA

At 390×844 in the in-app browser, the home search form and encoding preview stacked without horizontal overflow. `PI` navigated to `/search` without raw text in the URL, returned the verified first position 396, and showed readable occurrence rows. At desktop width, the result jump highlighted `1609` in Grid; the controls switched successfully to Spiral/Color Blocks and Line/Braille/Dark. At mobile width, the Line/Braille/Dark view retained its selected digit. `π🙂` first showed explicit Latin unsupported-input guidance; selecting UTF-8 produced a byte preview and a correctly scoped no-match message. These checks concern our app, not the reference's accuracy.
