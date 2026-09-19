# Body Pain Locator

A single-page web app that lets a person mark where they hurt on a rotatable 3D figure, describe
each site, and hand the result to a clinician.

`index.html` is the whole app — open it in a browser, or serve the folder. No build step and no
dependencies to install; three.js is pulled from a CDN at runtime.

## What it does

- **Three visualisations**, switchable from the left rail: **clothed** (the everyday view, easiest
  for pointing at a spot), **muscle map** (major muscle groups, colour-coded with a legend), and
  **nervous system** (a translucent body over the spinal cord, brachial plexus, intercostal roots,
  and the sciatic and femoral nerves).
- **Tap to mark.** Tapping the figure drops a pain point where the ray meets the body. The site is
  named automatically from the anatomy under the cursor — "Right lower back, to one side",
  "Back of thigh (hamstring)", "Base of spine (sacrum)" — and can be reviewed in the panel.
- **Per-point record**: intensity on the 0–10 numeric rating scale, character (sharp, burning,
  shooting, pins and needles…), pattern, duration, what it radiates into, and free-text notes.
- **Output for a clinician**: a plain-text summary to the clipboard, a structured JSON copy, and a
  print / save-as-PDF view with a table and a snapshot of the marked figure.

## Notes for reviewers

- **Not a diagnostic tool.** It records what a person reports. It does not assess, triage, score
  risk, or suggest a cause, and the disclaimer in the header says so.
- **No data leaves the browser.** There is no network call after the page loads. Points are held in
  memory only unless the person ticks "keep these points on this device", which writes to
  `localStorage` on that browser and nothing else. Every storage access is wrapped in `try`/`catch`
  so a private window or blocked storage degrades quietly.
- **Identifying data.** The UI asks people not to enter names or dates of birth, on the notes field
  and in the header. Before this is used with people who draw on our services, the wording and the
  retention position should be checked against our own data protection policy and privacy notice —
  those are the authoritative sources, not this README.
- **Accessibility.** The figure is keyboard-operable (arrow keys turn it, `+`/`−` zoom) and the
  point list is the text equivalent of what is marked, so the record is readable without the 3D
  view. The 3D view itself is not a substitute for a text description and should not be the only
  way to read a person's report.
- The anatomy is a schematic mannequin built from revolved profiles, not a scanned or
  clinically-validated model. It is accurate enough to point at a region; it is not accurate enough
  to localise a structure.

## Implementation

- three.js r128 (UMD from cdnjs, with a jsdelivr fallback). No model files — the CSP on some hosts
  blocks non-script assets, so the figure, the muscle overlays and the nerve tubes are all
  generated at runtime from `LatheGeometry` profiles, ellipsoids and `TubeGeometry` along
  Catmull-Rom curves.
- Orbit, pinch-zoom and pan are hand-rolled; r128's example controls are not published as a UMD
  global.
- Colours are converted from sRGB to linear on the way into every material — r128 predates
  three.js colour management, and skipping this bleaches the muscle map.
