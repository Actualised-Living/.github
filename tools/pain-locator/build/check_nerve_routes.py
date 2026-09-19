#!/usr/bin/env python3
"""Measure how closely the routed nerves hug real muscle tissue.

The peripheral nerves are drawn, not measured -- no open dataset has them. But
each waypoint is anchored to a named muscle's measured bounding box, so the
claim "these follow the muscles" is testable: every waypoint should sit close
to real muscle surface.

    node build/dump_routes.js > routes.json     # resolve the anchors in-page
    python3 build/check_nerve_routes.py routes.json

A NOTE ON WHAT NOT TO TEST. The obvious check -- "is the waypoint inside the
body" via trimesh's contains() against skin.glb -- does not work and silently
returns nonsense. BodyParts3D's skin is a thin shell rather than a solid, so
ray-parity reports the centre of the abdomen as outside. The decimated skin is
not watertight either. Distance to muscle is the test that actually means
something here.

Expected at the time of writing: 98 waypoints, median 3.1 mm from muscle,
8 beyond 30 mm -- all of them places a nerve genuinely leaves muscle and runs
over bone (the ulnar through Guyon's canal over the pisiform, the saphenous
over the medial face of the tibia, the radial's superficial branch across the
distal radius). Those are correct, not misses. A NEW outlier somewhere else is
what this script is for.
"""
import json, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
MUSCLES = os.path.join(HERE, "..", "assets", "muscles.glb")
LIMIT_MM = 30.0

def main():
    routes = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "routes.json"))
    sc = trimesh.load(MUSCLES)
    mus = trimesh.util.concatenate(list(sc.geometry.values()))
    pts, keys, unresolved = [], [], []
    for nerve, sides in routes.items():
        for side, qs in sides.items():
            for q in qs:
                if q["p"]:
                    pts.append(q["p"]); keys.append((nerve, side, q["m"]))
                else:
                    unresolved.append((nerve, side, q["m"]))
    for n, s, m in unresolved:
        print("  UNRESOLVED ANCHOR  %-8s %-5s %s" % (n, s, m))
    _, dist, _ = trimesh.proximity.closest_point(mus, np.array(pts))
    print("%d waypoints | distance to nearest muscle: median %.1f mm, 90th %.1f mm, max %.1f mm"
          % (len(pts), np.median(dist) * 1000, np.percentile(dist, 90) * 1000, dist.max() * 1000))
    far = [(k, d) for k, d in zip(keys, dist) if d * 1000 > LIMIT_MM]
    print("beyond %.0f mm: %d" % (LIMIT_MM, len(far)))
    for (n, s, m), d in sorted(far, key=lambda r: -r[1]):
        print("   %-8s %-5s %-34s %5.1f mm" % (n, s, m, d * 1000))
    per = {}
    for (n, _, _), d in zip(keys, dist):
        per.setdefault(n, []).append(d)
    print()
    for n, ds in per.items():
        print("   %-9s median %5.1f mm   worst %5.1f mm"
              % (n, np.median(ds) * 1000, max(ds) * 1000))
    return 1 if unresolved else 0

if __name__ == "__main__":
    sys.exit(main())
