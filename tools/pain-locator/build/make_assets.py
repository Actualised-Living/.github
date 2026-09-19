#!/usr/bin/env python3
"""
Convert BodyParts3D STL structures into web-ready glTF assets for the Body
Pain Locator.

Source: BodyParts3D, (c) The Database Center for Life Science,
licensed under CC Attribution-Share Alike 2.1 Japan.
https://lifesciencedb.jp/bp3d/

BodyParts3D space is millimetres, Z-up, +X = anatomical left. three.js wants
metres, Y-up, +Z = anterior. The rotation below is proper (determinant +1),
so left and right are preserved rather than mirrored -- which matters a great
deal when the output is a clinical record of which side hurts.
"""
import json, os, sys, time
import numpy as np
import trimesh
import fast_simplification

SRC = "/home/user/kevin-mattheus-moerman/bodyparts3d/assets/BodyParts3D_data"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

# Muscle name stems. BodyParts3D names muscles without the word "muscle"
# ("descending part of left trapezius"), so matching on "muscle" misses ~95%.
MUSCLE_STEMS = [
    "deltoid", "biceps", "triceps", "trapezius", "gastrocnemius", "gluteus",
    "latissimus", "rectus abdominis", "pectoralis", "sartorius", "soleus",
    "brachialis", "brachioradialis", "flexor", "extensor", "obliquus",
    "transversus abdominis", "serratus", "rhomboid", "teres", "supraspinatus",
    "infraspinatus", "subscapularis", "iliacus", "psoas", "adductor", "gracilis",
    "semitendinosus", "semimembranosus", "vastus", "rectus femoris", "tibialis",
    "peroneus", "fibularis", "sternocleidomastoid", "masseter", "temporalis",
    "levator", "piriformis", "tensor fasciae", "quadratus", "pronator",
    "supinator", "abductor", "opponens", "anconeus", "coracobrachialis",
    "plantaris", "popliteus", "erector", "splenius", "scalenus", "diaphragm",
    "intercostal", "gemellus", "obturator", "pectineus", "sphincter",
    "orbicularis", "palmaris", "lumbrical", "interosseus", "interossei",
    "digastric", "mylohyoid", "platysma", "longus", "longissimus", "iliocostalis",
    "multifidus", "intertransversarius", "rotatores", "spinalis", "semispinalis",
]

# Coarse group for colour-coding and the legend, tested in order.
GROUPS = [
    ("head/neck",  ["masseter", "temporalis", "sternocleidomastoid", "digastric",
                    "mylohyoid", "platysma", "orbicularis", "scalenus", "splenius",
                    "longus capitis", "longus colli"]),
    ("shoulder",   ["deltoid", "supraspinatus", "infraspinatus", "subscapularis",
                    "teres", "rhomboid", "levator scapulae", "serratus"]),
    ("upper back", ["trapezius", "latissimus"]),
    ("chest",      ["pectoralis", "intercostal", "diaphragm"]),
    ("abdomen",    ["rectus abdominis", "obliquus", "transversus abdominis",
                    "quadratus lumborum", "psoas", "iliacus"]),
    ("spine",      ["erector", "multifidus", "longissimus", "iliocostalis",
                    "spinalis", "semispinalis", "rotatores", "intertransversarius"]),
    ("upper arm",  ["biceps", "triceps", "brachialis", "coracobrachialis", "anconeus"]),
    ("forearm",    ["brachioradialis", "pronator", "supinator", "flexor carpi",
                    "extensor carpi", "flexor digitorum", "extensor digitorum",
                    "flexor pollicis", "extensor pollicis", "palmaris",
                    "extensor indicis", "abductor pollicis"]),

    ("foot",       ["hallucis", "plantae", "plantar", "of left foot", "of right foot",
                    "digitorum brevis", "digiti minimi brevis of left foot",
                    "digiti minimi brevis of right foot"]),
    ("hand",       ["lumbrical", "interosseus", "interossei", "opponens", "pollicis",
                    "abductor digiti minimi of", "flexor digiti minimi", "of left hand",
                    "of right hand", "palmaris brevis"]),
    ("hip/buttock",["gluteus", "piriformis", "gemellus", "obturator", "tensor fasciae",
                    "pectineus", "quadratus femoris"]),
    ("thigh",      ["vastus", "rectus femoris", "sartorius", "gracilis", "adductor",
                    "semitendinosus", "semimembranosus", "biceps femoris"]),
    ("lower leg",  ["gastrocnemius", "soleus", "tibialis", "peroneus", "fibularis",
                    "plantaris", "popliteus", "flexor hallucis", "extensor hallucis"]),

]

def group_of(name):
    low = name.lower()
    for g, stems in GROUPS:
        if any(s in low for s in stems):
            return g
    return "other"

def side_of(name):
    low = name.lower()
    if "left" in low:  return "left"
    if "right" in low: return "right"
    return "midline"

def load_names():
    names = {}
    with open(os.path.join(SRC, "parts_list_e.txt"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2:
                names[p[0]] = p[1]
    return names

# mm Z-up (+X left)  ->  metres Y-up (+Z anterior). Proper rotation, det = +1.
def to_three(v):
    return np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]) / 1000.0

def decimate(mesh, target):
    # STL stores every triangle with its own copy of each vertex, so the mesh
    # arrives with no shared edges at all and quadric collapse has nothing to
    # work with. Welding first is what makes decimation actually bite.
    mesh.merge_vertices()
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    n = len(mesh.faces)
    if n <= target:
        return mesh.vertices, mesh.faces
    reduction = 1.0 - (target / float(n))
    v, f = fast_simplification.simplify(
        np.asarray(mesh.vertices, dtype=np.float32),
        np.asarray(mesh.faces, dtype=np.int32),
        min(reduction, 0.995))
    return v, f

def build(kind, selection, names, budget, floor, ceil, offset=None, scale=None):
    """Load, decimate, transform and pack one set of structures into a GLB."""
    scene = trimesh.Scene()
    index, total_before, total_after = [], 0, 0
    t0 = time.time()
    for i, fid in enumerate(selection, 1):
        path = os.path.join(SRC, "stl", fid + ".stl")
        m = trimesh.load(path, process=False)
        before = len(m.faces)
        target = int(min(max(before * budget, floor), ceil))
        v, f = decimate(m, target)
        v = to_three(np.asarray(v, dtype=np.float64))
        if offset is not None:
            v = v + offset
        out = trimesh.Trimesh(vertices=v, faces=f, process=False)
        node = fid
        scene.add_geometry(out, node_name=node, geom_name=node)
        nm = names.get(fid, fid)
        lo, hi = v.min(axis=0), v.max(axis=0)
        index.append({"id": fid, "name": nm, "side": side_of(nm),
                      "group": group_of(nm), "tris": int(len(f)),
                      "bbox": [round(float(x), 4) for x in (*lo, *hi)]})
        total_before += before
        total_after += len(f)
        if i % 40 == 0 or i == len(selection):
            print("  %s %4d/%d  %7d -> %7d tris  (%.0fs)"
                  % (kind, i, len(selection), total_before, total_after, time.time() - t0),
                  flush=True)
    return scene, index, total_before, total_after

def landmarks(index_by_set):
    """Measure anatomical levels off the meshes themselves.

    The dermatome bands and the region thresholds in the app are expressed
    against these, so they follow the real body instead of numbers guessed
    against a schematic figure of a different height.
    """
    allrec = [r for recs in index_by_set.values() for r in recs]
    def over(sub, pick):
        hits = [r for r in allrec if sub in r["name"].lower()]
        if not hits: return None
        ys = [(r["bbox"][1], r["bbox"][4]) for r in hits]
        if pick == "top":    return round(max(h for _, h in ys), 4)
        if pick == "bottom": return round(min(l for l, _ in ys), 4)
        if pick == "mid":    return round(sum(l + h for l, h in ys) / (2 * len(ys)), 4)
    skin = [r for r in allrec if r["id"] == "FMA7163"]
    L = {
        "height":       round(skin[0]["bbox"][4], 4) if skin else None,
        "halfWidth":    round(max(abs(skin[0]["bbox"][0]), skin[0]["bbox"][3]), 4) if skin else None,
        "shoulderTop":  over("deltoid", "top"),
        "axilla":       over("deltoid", "bottom"),
        "nippleT4":     over("pectoralis major", "mid"),
        "costalMargin": over("rectus abdominis", "top"),
        "pubis":        over("rectus abdominis", "bottom"),
        "iliacCrest":   over("gluteus medius", "top"),
        "glutealFold":  over("gluteus maximus", "bottom"),
        "elbow":        over("brachialis", "bottom"),
        "wrist":        over("pronator quadratus", "bottom") or over("flexor carpi radialis", "bottom"),
        "kneeLine":     over("gastrocnemius", "top"),
        "ankle":        over("tibialis anterior", "bottom"),
    }
    return {k: v for k, v in L.items() if v is not None}


def main():
    os.makedirs(OUT, exist_ok=True)
    names = load_names()
    have = {p[:-4] for p in os.listdir(os.path.join(SRC, "stl")) if p.endswith(".stl")}

    muscles = sorted(fid for fid in have
                     if any(s in names.get(fid, "").lower() for s in MUSCLE_STEMS))
    print("muscle structures selected: %d" % len(muscles))

    # The skin defines the shared frame: centre it on X/Z and stand it on y = 0,
    # then apply the identical offset to every other set so they stay registered.
    print("measuring skin for a shared frame...", flush=True)
    skin_raw = trimesh.load(os.path.join(SRC, "stl", "FMA7163.stl"), process=False)
    sv = to_three(np.asarray(skin_raw.vertices, dtype=np.float64))
    lo, hi = sv.min(axis=0), sv.max(axis=0)
    offset = np.array([-(lo[0] + hi[0]) / 2.0, -lo[1], -(lo[2] + hi[2]) / 2.0])
    print("  skin bounds (m): %s .. %s" % (np.round(lo, 3), np.round(hi, 3)))
    print("  height: %.3f m   offset applied: %s" % (hi[1] - lo[1], np.round(offset, 3)))
    del skin_raw, sv

    sets = {
        "skin":    (["FMA7163"], 0.05, 40000, 70000),
        "muscles": (muscles,     0.04,   250,   2200),
    }
    manifest = {
        "source": "BodyParts3D, (c) The Database Center for Life Science, "
                  "licensed under CC Attribution-Share Alike 2.1 Japan",
        "sourceUrl": "https://lifesciencedb.jp/bp3d/",
        "licence": "CC BY-SA 2.1 Japan",
        "frame": {"units": "metres", "up": "+Y", "anterior": "+Z",
                  "left": "+X", "feet": "y = 0"},
        "sets": {},
    }
    for kind, (sel, budget, floor, ceil) in sets.items():
        print("\nbuilding %s (%d structures)..." % (kind, len(sel)), flush=True)
        scene, index, before, after = build(kind, sel, names, budget, floor, ceil, offset)
        dest = os.path.join(OUT, kind + ".glb")
        scene.export(dest)
        mb = os.path.getsize(dest) / 1e6
        print("  wrote %s  %.1f MB  (%d -> %d tris, %.1f%%)"
              % (dest, mb, before, after, 100.0 * after / max(before, 1)))
        manifest["sets"][kind] = {"file": kind + ".glb", "count": len(index),
                                  "triangles": after, "megabytes": round(mb, 2),
                                  "structures": index}
    manifest["landmarks"] = landmarks(
        {k: v["structures"] for k, v in manifest["sets"].items()})
    print("\nlandmarks (metres above the floor):")
    for k, v in manifest["landmarks"].items():
        print("  %-13s %.3f" % (k, v))
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print("\nwrote manifest.json")

if __name__ == "__main__":
    main()
