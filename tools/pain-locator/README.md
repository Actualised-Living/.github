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

## Real anatomy

`build/make_assets.py` converts the [BodyParts3D](https://lifesciencedb.jp/bp3d/) dataset into
web-ready glTF, and the app loads it at startup.

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

### Asset loading

The app fetches `manifest.json`, `skin.glb` and `muscles.glb` from `assets/` by default. Point it
elsewhere with `?assets=<base-url>` on the URL, or by setting `window.PAIN_LOCATOR_ASSETS` before the
page script runs — that is the hook for serving them out of attachment storage.

**If the assets do not load the app still works.** The schematic figure stays on screen, all four
visualisations keep working, and the rail says so plainly rather than failing.

### What a tap now records

Tapping the body produces three things instead of one:

- **Region** in plain English — "Right lower back, to one side".
- **Approximate spinal level** — the dermatome, reported with its neighbours (`T10 · approx T9–T11`).
- **The muscle beneath the point** — a ray is cast inward from the surface and the first muscle it
  meets is named from the data: "long head of right biceps femoris", "ascending part of right
  trapezius". Reach is capped at 85 mm so the answer is what lies under the point, not whatever the
  ray eventually exits through.

### Dermatomes

A fourth visualisation shades the body by spinal nerve level, C2–S5, with the face marked as
trigeminal rather than spinal. Levels are anchored on the ISNCSCI key sensory points — T4 at the
nipple line, T10 at the navel, L5 the great toe, S1 the little toe — and the two trunk anchors are
measured off the meshes, so the bands follow the actual body.

**These boundaries are approximate and the app says so.** Published dermatome charts genuinely
disagree with one another, and adjacent dermatomes overlap substantially on a real person, so every
reading is reported as a band rather than an edge. Posterior bands carry a fixed two-segment offset
to approximate the downward-and-forward obliquity of a real dermatome; that offset is a
simplification. A clinician should review the mapping before it is relied on.

Colour encoding: four region hues (cervical, thoracic, lumbar, sacral), each stepped light to dark
across its levels, because the levels are ordered rather than merely categorical. The hues were
checked for colour-vision separation and contrast against the stage in both themes. Identity is
never carried by colour alone — the level is named in the read-out, the point list, the detail card
and the printed table.

Validated against known anatomy (see `build/`): nipple line → T4 over pectoralis major; navel → T10;
lateral shin → L5 over tibialis anterior; back of calf → S1 over gastrocnemius; back of thigh → S2
over biceps femoris; thumb side of hand → C6; little finger → C8 over abductor digiti minimi.

### The nervous system: partly solved, and the limits matter

`nerves.glb` (0.38 MB) carries the **spinal dura and the dorsal root ganglia**, exported from
[Z-Anatomy](https://www.z-anatomy.com/) (CC BY-SA 4.0) and registered onto this frame. The cord
follows the vertebral canal with the right curvature and ends near the conus at L1/L2, as it should.

**Neither open dataset models the peripheral nervous system.** BodyParts3D has no peripheral nerves
at all. Z-Anatomy's nervous system collection is central only — brain, cerebellum, brainstem,
ventricles, cord, ganglia, eye; its apparent "sciatic" and "ulnar" entries are the *greater sciatic
foramen* and *extensor carpi ulnaris*, a bone feature and a muscle. So the limb and rib branches in
the nerve view are still **drawn, not measured**, and the on-screen legend says exactly that.

If a genuinely accurate peripheral nerve map is needed, it has to come from a licensed commercial
dataset — the free ones do not have one.

Rebuild it with `build/extract_nerves.blender.py` (needs Blender) followed by `build/make_nerves.py`;
both are documented in their own docstrings.

### Embedding the assets instead of serving them

`window.PAIN_LOCATOR_ASSET_MAP` overrides the fetch location per file, so an embedder can hand the
three assets over directly rather than exposing a folder:

```html
<script>window.PAIN_LOCATOR_ASSET_MAP = {
  "manifest.json": "https://…/manifest.json",   // or a signed attachment-storage URL
  "skin.glb":      "data:model/gltf-binary;base64,…",
  "muscles.glb":   "https://…/muscles.glb"
};</script>
```

`build/make_standalone.py` uses this to bake everything into one ~12 MB file that runs with no
network and nothing beside it — handy for sending to a reviewer.
