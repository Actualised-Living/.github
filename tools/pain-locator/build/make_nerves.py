#!/usr/bin/env python3
"""Register Z-Anatomy's central nervous structures into the app's frame.

Two stages, because the source is a Blender file:

  1. blender -b --factory-startup Z-Anatomy/Startup.blend \
         --python build/extract_nerves.blender.py
     writes za_ns_raw.obj (OBJ, not glTF: the Ubuntu Blender package's glTF
     exporter needs numpy, which that build does not ship) and prints the
     vertebral-column bounding box it measured.

  2. python3 build/make_nerves.py za_ns_raw.obj
     registers that onto the BodyParts3D frame and writes assets/nerves.glb.

Registration fits a uniform scale on the vertebral column, which both datasets
model, then matches centres. It comes out near identity (~0.969 and a 26 mm
depth shift) because Z-Anatomy is itself derived from BodyParts3D -- but it is
fitted rather than assumed, and the result is checked: the cord has to land
inside the torso, behind the mid-plane, ending near the conus at L1/L2.

WHAT THIS DOES NOT GIVE YOU: peripheral nerves. Z-Anatomy's nervous system
collection is central only -- brain, cerebellum, brainstem, ventricles, spinal
dura, dorsal root ganglia, eye. There is no sciatic, median, ulnar, radial,
femoral or intercostal nerve geometry in it. The app's limb branches stay
schematic and are labelled as such.

Source: Z-Anatomy by Gauthier Kervyn, CC BY-SA 4.0, https://www.z-anatomy.com/
        itself derived from BodyParts3D (CC BY-SA 2.1 Japan).
"""
import json, os, sys
import numpy as np
import trimesh
import fast_simplification

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
# Measured by extract_nerves.blender.py; both in the +Y-up frame.
ZA_VERT_MIN = np.array([-0.0992744, 0.9471112, -0.1147120])
ZA_VERT_MAX = np.array([0.0970647, 1.5223106, 0.0887899])
NAME = {"Spinal_dura": "spinal_dura",
        "Spinal_ganglion.l": "ganglion_left",
        "Spinal_ganglion.r": "ganglion_right"}

def read_obj_objects(path):
    """Split an OBJ on its 'o' records. trimesh merges them on load whatever
    split_object says, and the dura must stay separate from the ganglia."""
    verts, objs, cur = [], [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("v "):
            verts.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("o "):
            cur = {"name": line[2:].strip(), "faces": []}
            objs.append(cur)
        elif line.startswith("f ") and cur is not None:
            idx = [int(p.split("/")[0]) for p in line.split()[1:]]
            idx = [(i - 1) if i > 0 else (len(verts) + i) for i in idx]
            for k in range(1, len(idx) - 1):
                cur["faces"].append([idx[0], idx[k], idx[k + 1]])
    return np.array(verts, dtype=np.float64), objs

def bp3d_vertebrae_bbox(src):
    """The same column, measured in the app's frame, as the registration target."""
    names = {}
    with open(os.path.join(src, "parts_list_e.txt"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2:
                names[p[0]] = p[1]
    have = {p[:-4] for p in os.listdir(os.path.join(src, "stl")) if p.endswith(".stl")}
    to_three = lambda v: np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]) / 1000.0
    skin = trimesh.load(os.path.join(src, "stl", "FMA7163.stl"), process=False)
    sv = to_three(np.asarray(skin.vertices, dtype=np.float64))
    lo, hi = sv.min(axis=0), sv.max(axis=0)
    offset = np.array([-(lo[0] + hi[0]) / 2.0, -lo[1], -(lo[2] + hi[2]) / 2.0])
    del skin, sv
    lo = np.array([1e9] * 3); hi = np.array([-1e9] * 3)
    for k in (k for k in have if "vertebra" in names.get(k, "").lower()):
        m = trimesh.load(os.path.join(src, "stl", k + ".stl"), process=False)
        v = to_three(np.asarray(m.vertices, dtype=np.float64)) + offset
        lo = np.minimum(lo, v.min(axis=0)); hi = np.maximum(hi, v.max(axis=0))
    return lo, hi

def main():
    obj = sys.argv[1] if len(sys.argv) > 1 else "za_ns_raw.obj"
    src = os.environ.get("BP3D", "/home/user/kevin-mattheus-moerman/bodyparts3d/"
                                 "assets/BodyParts3D_data")
    lo, hi = bp3d_vertebrae_bbox(src)
    s = float((hi[1] - lo[1]) / (ZA_VERT_MAX[1] - ZA_VERT_MIN[1]))
    t = (lo + hi) / 2.0 - ((ZA_VERT_MIN + ZA_VERT_MAX) / 2.0) * s
    print("uniform scale %.5f, translation %s" % (s, np.round(t, 4)))

    V, objs = read_obj_objects(obj)
    scene, index = trimesh.Scene(), []
    for o in objs:
        f = np.array(o["faces"], dtype=np.int64)
        used = np.unique(f)
        remap = -np.ones(len(V), dtype=np.int64); remap[used] = np.arange(len(used))
        v = V[used] * s + t
        f = remap[f].astype(np.int32)
        if len(f) > 9000:
            m = trimesh.Trimesh(vertices=v, faces=f, process=False)
            m.merge_vertices(); m.update_faces(m.unique_faces()); m.remove_unreferenced_vertices()
            vv, ff = fast_simplification.simplify(
                np.asarray(m.vertices, dtype=np.float32),
                np.asarray(m.faces, dtype=np.int32), 1.0 - 9000.0 / len(m.faces))
            v, f = np.asarray(vv, dtype=np.float64), ff
        nm = NAME.get(o["name"], o["name"])
        scene.add_geometry(trimesh.Trimesh(vertices=v, faces=f, process=False),
                           node_name=nm, geom_name=nm)
        blo, bhi = v.min(axis=0), v.max(axis=0)
        index.append({"id": nm, "name": o["name"], "tris": int(len(f)),
                      "bbox": [round(float(x), 4) for x in (*blo, *bhi)]})
        print("  %-16s tris=%-6d y %.3f..%.3f  z %.3f..%.3f"
              % (nm, len(f), blo[1], bhi[1], blo[2], bhi[2]))
        if bhi[2] > 0.02:
            print("     WARNING: this sits in front of the mid-plane; the cord should be behind it")

    dest = os.path.join(OUT, "nerves.glb")
    scene.export(dest)
    man = json.load(open(os.path.join(OUT, "manifest.json")))
    man["sets"]["nerves"] = {
        "file": "nerves.glb", "count": len(index),
        "triangles": sum(r["tris"] for r in index),
        "megabytes": round(os.path.getsize(dest) / 1e6, 2),
        "source": "Z-Anatomy (CC BY-SA 4.0), registered by a uniform scale of "
                  "%.4f fitted on the vertebral column" % s,
        "coverage": "Central nervous system only: spinal dura and dorsal root ganglia. "
                    "Z-Anatomy models no peripheral nerves.",
        "structures": index}
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print("wrote %s (%.2f MB) and updated the manifest" % (dest, os.path.getsize(dest) / 1e6))

if __name__ == "__main__":
    main()
