#!/usr/bin/env python3
"""Produce a reduced-detail asset set for phones and inline previews.

The full set is ~9 MB of glTF, which bakes into a ~13 MB single file. That is
fine on a desktop and too heavy for a phone preview, and 390k triangles is a
lot for a mobile GPU besides.

This re-decimates the built assets rather than re-running the STL pipeline, so
the registration, the naming and the landmarks stay exactly as they were. The
manifest is copied across untouched apart from file sizes: the app reads
per-structure bounding boxes from it to anchor the nerve routes and the
dermatome bands, and those must not shift between the two builds.

    python3 build/make_assets.py && python3 build/make_nerves.py …   # full set
    python3 build/make_lite.py                                       # then this
"""
import json, os, shutil, sys
import numpy as np
import trimesh
import fast_simplification

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "assets")
OUT = os.path.join(SRC, "lite")
# triangle budget per set
BUDGET = {"muscles": 70000, "skin": 22000, "bones": 14000, "nerves": 9000}
FLOOR = 40          # never reduce one structure below this many triangles

def shrink(path, dest, budget):
    sc = trimesh.load(path)
    geoms = sc.geometry if hasattr(sc, "geometry") else {"mesh": sc}
    before = sum(len(g.faces) for g in geoms.values())
    ratio = min(1.0, float(budget) / max(before, 1))
    out = trimesh.Scene()
    after = 0
    for name, g in geoms.items():
        v = np.asarray(g.vertices, dtype=np.float64)
        f = np.asarray(g.faces, dtype=np.int32)
        target = max(FLOOR, int(len(f) * ratio))
        if target < len(f):
            m = trimesh.Trimesh(vertices=v, faces=f, process=False)
            m.merge_vertices(); m.update_faces(m.unique_faces()); m.remove_unreferenced_vertices()
            if len(m.faces) > target:
                vv, ff = fast_simplification.simplify(
                    np.asarray(m.vertices, dtype=np.float32),
                    np.asarray(m.faces, dtype=np.int32),
                    min(1.0 - target / float(len(m.faces)), 0.995))
                v, f = np.asarray(vv, dtype=np.float64), ff
            else:
                v, f = np.asarray(m.vertices), np.asarray(m.faces)
        out.add_geometry(trimesh.Trimesh(vertices=v, faces=f, process=False),
                         node_name=name, geom_name=name)
        after += len(f)
    out.export(dest)
    return before, after, os.path.getsize(dest)

def main():
    os.makedirs(OUT, exist_ok=True)
    man = json.load(open(os.path.join(SRC, "manifest.json")))
    total = 0
    for kind, budget in BUDGET.items():
        src = os.path.join(SRC, kind + ".glb")
        if not os.path.exists(src):
            print("  skipping %s (not built)" % kind); continue
        before, after, size = shrink(src, os.path.join(OUT, kind + ".glb"), budget)
        total += size
        print("  %-8s %7d -> %6d tris   %5.2f MB" % (kind, before, after, size / 1e6))
        if kind in man["sets"]:
            man["sets"][kind]["triangles"] = after
            man["sets"][kind]["megabytes"] = round(size / 1e6, 2)
    man["variant"] = ("reduced detail for phones and previews; geometry decimated, "
                      "naming, bounding boxes and landmarks identical to the full set")
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print("  total %.2f MB of glTF in %s" % (total / 1e6, OUT))

if __name__ == "__main__":
    main()
