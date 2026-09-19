# Body Pain Locator

A single-page web app that lets a person mark where they hurt on a rotatable 3D figure, describe
each site, and hand the result to a clinician.

`index.html` is the whole app — open it in a browser by double-clicking it, or serve the folder.
No build step, nothing to install, and no network: three.js is inlined into the file, so it works
offline and on a machine with no route out.

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
- **No data leaves the browser.** The page makes no network calls at all — not on load, not after.
  The only external reference left is the Google Fonts stylesheet, which is optional: block it and
  the page falls back to system fonts and is otherwise unchanged. Points are held in
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

- three.js r128 (the UMD build from npm `three@0.128.0`, MIT, sha256
  `9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2`) is inlined verbatim with its
  licence banner. It is the only third-party code in the file and accounts for most of its size;
  the app itself is about 70 KB. No model files either — the figure, the muscle overlays and the
  nerve tubes are all generated at runtime from `LatheGeometry` profiles, ellipsoids and
  `TubeGeometry` along Catmull-Rom curves.
- Orbit, pinch-zoom and pan are hand-rolled; r128's example controls are not published as a UMD
  global.
- Colours are converted from sRGB to linear on the way into every material — r128 predates
  three.js colour management, and skipping this bleaches the muscle map.

## Real anatomy (work in progress)

`build/make_assets.py` converts the [BodyParts3D](https://lifesciencedb.jp/bp3d/) dataset into
web-ready glTF for the app. It is **not yet wired into `index.html`** — the app still draws the
schematic figure described above.

Run it against a clone of
[Kevin-Mattheus-Moerman/BodyParts3D](https://github.com/Kevin-Mattheus-Moerman/BodyParts3D)
(adjust `SRC` at the top). It writes into `assets/`:

| file | contents | size | triangles |
|---|---|---|---|
| `muscles.glb` | 339 individually named muscle structures, FMA-indexed | 7.2 MB | 390k |
| `skin.glb` | body surface, used as the hit target and the outer shell | 1.2 MB | 70k |
| `manifest.json` | per-structure name, side, muscle group and triangle count | 52 KB | — |

The `.glb` files are gitignored: they are reproducible from the pipeline and belong in attachment
storage. See `assets/ATTRIBUTION.md` for the required credit and the ShareAlike question.

**Why this matters for naming.** Every mesh carries its FMA identifier, so a tap can be reported as
"descending part of the left trapezius" straight from the data, rather than inferred from
coordinates as the schematic version does.

**Coordinate frame.** BodyParts3D is millimetres, Z-up, +X anatomical left. The pipeline rotates to
the app's metres, Y-up, +Z anterior, feet on `y = 0`. The rotation has determinant +1, so left and
right are preserved — verified by checking that "acromial part of left deltoid" lands at positive X.
Getting this backwards would silently put every pain point on the wrong side of the body.

### The nervous system is not solved

BodyParts3D contains no peripheral nervous system. There is no sciatic, median, ulnar, radial or
femoral nerve in the dataset — only the spinal cord, the optic nerves and the choroid plexus. The
nerve view in the app therefore remains **schematic and should be labelled as such**. Options:

- Export the peripheral nerves from [Z-Anatomy](https://www.z-anatomy.com/) (CC BY-SA 4.0), which
  models them. It ships as a Blender file, so it needs a Blender export step this pipeline does not
  do; the resulting `.glb` would drop into `assets/` alongside the others.
- Replace the nerve view with a **dermatome map**, which is arguably more useful for a pain locator
  since it maps a site to a spinal level. Note that published dermatome charts genuinely disagree
  with one another, so a source has to be chosen and cited on the page.
