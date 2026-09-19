# Publishing the Body Map as a ZS report

A ZS report is a database record, not a file in a repository: the template is
stored on the `forms` row `ZsReport Configuration - <title>` and promoted into
the `zsreports` table. There is nothing to commit to a tenant, and `hcsx` is a
tenant (`zonestandard.hcsx.co.uk`), not a repo. Everything below happens in the
portal.

Regenerate the three inputs first — they are gitignored, being derived:

    python3 build/make_zsreport.py                 # full detail
    python3 build/make_zsreport.py zsreport assets/lite   # phone-sized meshes

| File | What it is |
|---|---|
| `template.html` | the report template — paste into the editor |
| `three-r128-bundle.js` | three.js r128 + GLTFLoader, ~700 KB — upload as an attachment |
| `settings-assets.json` | the `settings.assets` rows, URLs stubbed |

## 1 · Upload the attachments

Upload these six files to attachment storage in the tenant, keeping them
together in one attachment directory:

    three-r128-bundle.js  manifest.json  skin.glb  muscles.glb  bones.glb  nerves.glb

Full detail is about 10 MB, `assets/lite` about 2.6 MB. Use lite if the report
will be opened on phones.

## 2 · Fill in the asset URLs

Each row in `settings-assets.json` has a placeholder URL of the form

    /form/attachment/view/REPLACE-WITH-ATTACHMENT-DIRECTORY/skin.glb/

Replace `REPLACE-WITH-ATTACHMENT-DIRECTORY` with the directory the upload
produced. Keep the route root-relative: it keeps the portal's own access
controls and redirects to a freshly signed blob on each request. Do not paste a
signed blob URL — those expire, and the report would break silently later.

Until the placeholders are replaced, the report renders a notice naming the
assets still unset rather than a blank page.

## 3 · Create the report

At `https://zonestandard.<tenant>/zsreport/edit/` — needs **ZsReport Edit** or
**Form Config**:

- **Template** — paste `template.html`.
- **Data** — `{}`. Nothing in the template reads report data.
- **Assets** — one row per entry in `settings-assets.json`.
- **Print button** — leave **off**. The template is a whole HTML document; the
  print wrapper would nest it inside another page.
- Leave view/data column and filter/URL parameter unset: this is a
  stored-data report, not a view-backed one.

To preview inside the editor, turn **Same-origin preview** on. The default
sandbox has no `allow-same-origin`, so portal attachments will not load and a
working report will look broken.

Published, it serves at `/zsreport/view/<title>`.

## Who can see the anatomy

The attachment routes are behind the `form_attachment_view` privilege. A viewer
who can open the report but lacks that privilege gets the schematic fallback
figure and a note saying the assets did not load — not an error, but not the
real anatomy either. Decide the audience before publishing.

## What the template does differently from `index.html`

- **three.js is not inlined.** It loads from the `threeBundle` asset, and the
  app's existing `window.__boot3d` hook starts the scene once it arrives. This
  keeps the template around 100 KB instead of 800 KB, so it stays editable.
- **Assets come from `zsr.assets`.** The renderer deliberately does not fetch
  files or load listed scripts, so the template resolves the keys itself and
  fills the app's `PAIN_LOCATOR_ASSET_MAP` hook.
- **The Google Fonts link is removed.** A report served from a care-sector
  portal should not make every viewer's browser call a third party. Each font
  stack already names system fallbacks. Pass `--keep-webfonts` to leave it in.
- **The app is wrapped in `{% raw %}`** so a future edit containing `{{` or
  `{%` cannot be eaten by Jinja.

## Before it goes live

The anatomy is **BodyParts3D** (CC BY-SA 2.1 Japan) and **Z-Anatomy**
(CC BY-SA 4.0). Both are share-alike. Attribution is shown in the app, but
someone at Actualised Living needs to own the licensing position for publishing
this to a tenant — it is not a decision this build makes.

The in-app banner already says the map is an anatomical reference and not a
clinical instrument, that dermatome boundaries are approximate and the
peripheral nerves are drawn rather than measured. Keep that visible.
