# Attribution and licence for the anatomical assets

`skin.glb` and `muscles.glb` in this folder are **derived works**. They were produced by
`../build/make_assets.py`, which selects structures from BodyParts3D, welds and decimates the
meshes, and re-expresses them in the app's coordinate frame.

## Required credit

The licence requires this credit to be displayed wherever the assets are used:

> BodyParts3D, Copyright © 2008 Life Science Integrated Database Center
> licensed by CC Attribution-Share Alike 2.1 Japan

Source: <https://lifesciencedb.jp/bp3d/> · Licence: <https://creativecommons.org/licenses/by-sa/2.1/jp/deed.en>

Cite also the source paper and the data archive DOI `10.18908/lsdba.nbdc00837-000`.

## ShareAlike — read before shipping

CC BY-SA is a **copyleft** licence. Distributing these meshes, or anything built from them, may
oblige us to release that work under the same licence and to carry the credit above in the product
itself, not just in this file. Whether that is acceptable, and whether a BY-SA 2.1 Japan work can be
redistributed under a later BY-SA version, are decisions for whoever owns licensing at Actualised
Living — **not** questions this file settles. Check against the Creative Commons compatibility
guidance and take advice before these assets go into anything distributed outside the organisation.

## What the meshes are and are not

They are derived from real anatomical data, so the shapes and the names are sound. That does not
make the app a clinical instrument. The structures have not been checked, one by one, against an
anatomical authority by anyone qualified to do so. Before this is relied on in care documentation,
a clinician should review the naming and the placement.

## Second source: Z-Anatomy

`nerves.glb` derives from **Z-Anatomy** by Gauthier Kervyn, licensed **CC BY-SA 4.0**
(<https://www.z-anatomy.com/>), which is itself built on BodyParts3D. Required credit:

> Z-Anatomy, Gauthier Kervyn, CC BY-SA 4.0 — derived from BodyParts3D,
> © The Database Center for Life Science, CC BY-SA 2.1 Japan

**This makes the licensing question sharper, not softer.** Two ShareAlike licences of different
versions are now in play — CC BY-SA 2.1 Japan and CC BY-SA 4.0. Whether they can be combined, and
under what licence the combined work must be released, is a question for whoever owns licensing at
Actualised Living, checked against Creative Commons' own compatibility guidance. Nothing here
settles it.

**What it contains, and what it does not.** Only the spinal dura and the dorsal root ganglia are
used, because Z-Anatomy's nervous system is central only: brain, cerebellum, brainstem, ventricles,
cord, ganglia, eye. It models **no peripheral nerves** — no sciatic, median, ulnar, radial, femoral
or intercostal nerve geometry exists in it. The app's limb and rib branches remain drawn rather
than measured, and the legend says so on screen.
