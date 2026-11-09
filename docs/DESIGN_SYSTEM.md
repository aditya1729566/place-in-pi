# Design system — Pi Dictionary

Subject: an instrument for locating exact digit patterns in π. Audience: curious readers, students, and researchers. The primary job is to turn text into a transparent numeric pattern and show what was actually found.

## Direction

An oceanographic observatory rather than a neon game: the corpus is a navigable field, and position markers behave like instrument coordinates. The signature element is a digit ruler that aligns encoding, match position, and local context. Search evidence remains in semantic HTML while a canvas handles dense exploration.

| Token | Value | Use |
| --- | --- | --- |
| Ink | `#183442` | headings, dark surfaces |
| Deep | `#102630` | dark theme background |
| Chalk | `#f2f6f3` | light background |
| Mist | `#dce9e5` | panels, rules |
| Coral | `#cf694f` | selected match and actions |
| Iris | `#7774ad` | secondary data |

Display: Georgia or Iowan Old Style, used only for the main thesis and section headings. Body: Avenir Next or system sans. Data: ui-monospace. Large type carries the invitation; small caps and monospaced figures label measured quantities. Minimum body size 15px. Space scale: 4, 8, 12, 16, 24, 32, 48, 72px. Content max width 1280px; wide split at 900px, compact stack below it, narrow controls below 600px.

The ten digit colors are distinct from the match outline; each has a printed label in the legend. Dark and light themes preserve contrast. Focus rings are 3px coral or iris with offset. Canvas state is mirrored by a semantic context strip and screen-reader summary. Motion is limited to a short viewport transition and disabled with `prefers-reduced-motion`.
