# Body Map

An interactive anatomical body map. A rotatable figure with five overlays; clicking any part of the
body opens a small panel naming what is there.

`index.html` is the whole app — open it in a browser by double-clicking it, or serve the folder.
No build step and nothing to install. The anatomy assets load from `assets/`, or can be embedded
(see below) so the file runs with no network at all.

## What it does

- **Five overlays**, switchable from the left rail: **body surface**, **muscle map** (339 named
  structures over the skeleton), **muscle pairs** (agonist against antagonist, one joint at a
  time), **nervous system** (measured spinal cord and ganglia, with the peripheral branches routed
  through the muscles), and **dermatomes** (spinal levels C2–S5).
- **Click anything** and a panel names the region, the muscle beneath the point and its FMA
  identifier, what that muscle works against, and the approximate spinal level.
- Hovering gives the same in one line along the top of the stage.

## Notes for reviewers

- **It is a reference, not a clinical instrument.** The structures and names come from open
  anatomical datasets. Dermatome boundaries are approximate and published charts disagree; the
  peripheral nerves are drawn rather than measured, because no open dataset models them. The app
  says so on screen. A clinician should confirm anything relied on.
- **Nothing is collected or stored.** The app takes no input, writes nothing to the browser, and
  makes no network call once loaded. It previously recorded pain points; that layer was removed
  when the focus moved to the body map, and is recoverable from git history if wanted.
- **Accessibility.** The figure is keyboard-operable (arrow keys turn it, `+`/`−` zoom, `Esc`
  closes the panel). The 3D view is not a substitute for a text description of anatomy.

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
| `bones.glb` | 112 structures: skull, vertebral column, ribcage, discs and costal cartilage | 1.3 MB | 67k |
| `nerves.glb` | spinal dura and dorsal root ganglia (Z-Anatomy) | 0.4 MB | 24k |
| `manifest.json` | per-structure name, side, muscle group and triangle count | 52 KB | — |

The `.glb` files are gitignored: they are reproducible from the pipeline and belong in attachment
storage. See `assets/ATTRIBUTION.md` for the required credit and the ShareAlike question.

**Why this matters for naming.** Every mesh carries its FMA identifier, so a tap can be reported as
"descending part of the left trapezius" straight from the data, rather than inferred from
coordinates as the schematic version does.

**Why the bones are there.** Without a cranium, temporalis and the facial muscles hang in space and
read as a pair of horns above the head; without a column, the neck and deep back muscles float too.
Two selector traps: `hyoid` matches six muscles (genio-, omo-, sterno-, stylo-, thyro-, mylohyoid)
as well as the hyoid bone, and `vertebra` matches the intervertebral discs as well as the vertebrae.
The first is excluded, the second is kept deliberately — disc pathology drives a large share of the
back pain this tool records — and discs are tagged `kind: "disc"` in the manifest so the app can
render them as cartilage rather than bone. The ribcage — 24 ribs, sternum, manubrium, xiphoid and 16 costal cartilages — is included too;
cartilage is tagged `kind: "cartilage"` and renders like the discs rather than like bone. The
clavicles and scapulae are in the dataset and remain the obvious next addition, since the shoulder
pairing's muscles attach to them.

The skeleton is solid behind the muscle views and a faint ghost behind the nerve view: the
intercostal nerves only read as intercostals when there are ribs for them to run between.

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

### Muscle pairs

A fifth visualisation shows agonist and antagonist across one joint at a time: eleven pairings from
shoulder to foot inversion. The selected pairing's two poles take a validated diverging pair, one
warm and one cool, and every other muscle steps back to a translucent neutral.

**One pairing at a time, because biarticular muscles belong to two.** Rectus femoris flexes the hip
*and* extends the knee; gastrocnemius flexes the knee *and* plantarflexes the ankle. Colouring all
eleven at once would have to pick one membership per muscle and silently drop the other.

Hovering names the relationship — "right brachioradialis · flexion, against extension" — and a pain
point recorded over a mapped muscle carries the pairing into the clinician summary. That is the
point of the feature: where tone is raised on one side of a joint the other is often held long and
weak, and the pain someone reports can sit in the stretched partner rather than the tight one, so a
record naming the pairing is more use than one naming a single muscle.

**The pairings are anatomy and nothing more.** The app makes no claim about which side becomes
spastic: the usual patterns differ between the upper limb and the lower, and between lesions, and
that is a clinical judgement rather than something to encode in a colour. The on-screen note says
so. A clinician should confirm the groupings before they are relied on.

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

**But the branches are no longer guesses.** A peripheral nerve is defined clinically by the muscles
it runs between, so each waypoint names a muscle and a face of it, and its position comes from that
muscle's measured bounding box: the ulnar behind the medial epicondyle where flexor carpi ulnaris
begins, the sciatic between biceps femoris and semimembranosus, the tibial deep to soleus, the
median through the two heads of pronator teres and into the carpal tunnel under the flexor
retinaculum. Change the body and the routes follow it.

`build/check_nerve_routes.py` measures the result: **98 waypoints, median 3.1 mm from real muscle
surface.** Eight sit beyond 30 mm, and all eight are places a nerve genuinely leaves muscle and runs
over bone — the ulnar through Guyon's canal over the pisiform, the saphenous over the medial face of
the tibia, the radial's superficial branch across the distal radius. Those are correct, not misses.

One thing that script documents at length because it cost time: **do not check this with
`contains()` against the skin.** BodyParts3D's skin is a thin shell, not a solid, so ray-parity
reports the centre of the abdomen as outside the body. It returns confident nonsense.

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

`build/make_standalone.py` uses this to bake everything into one self-contained file that runs with
no network and nothing beside it — handy for sending to a reviewer.

### Two builds: desktop and phone

The full asset set is ~9 MB of glTF and bakes into a **13 MB** single file. That is fine on a
desktop and too heavy for a phone: it exceeds what chat clients will preview inline, and 390k
triangles is a lot for a mobile GPU.

`build/make_lite.py` re-decimates the built assets into `assets/lite/` — 2.3 MB of glTF, a **4 MB**
single file that loads in under three seconds at phone size. It re-decimates the *built* assets
rather than re-running the STL pipeline, so registration, naming, bounding boxes and landmarks are
identical between the two builds. That matters: the app reads per-structure bounding boxes from the
manifest to anchor the nerve routes and the dermatome bands, so the two builds must agree.

```sh
python3 build/make_standalone.py out.html              # full detail, ~13 MB
python3 build/make_lite.py
python3 build/make_standalone.py out.html assets/lite  # reduced, ~4 MB
```

On phones the layout puts the figure directly under the header, with the controls below it —
otherwise you scroll past three sections of rail before the body appears.
