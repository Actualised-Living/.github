#!/usr/bin/env python3
"""Bake index.html plus the anatomy assets into one self-contained file.

The result needs no network and no folder beside it: three.js and GLTFLoader
are already inlined in index.html, and this embeds the meshes as data URIs
through the PAIN_LOCATOR_ASSET_MAP hook. About 12 MB.

    python3 build/make_standalone.py [output.html] [assets-dir]

Pass assets/lite as the second argument for the reduced-detail build, which is
about 4 MB instead of 13 and will load on a phone.
"""
import base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "index.html")
ASSETS = os.path.join(HERE, "..", "assets")
MIME = {"manifest.json": "application/json",
        "skin.glb": "model/gltf-binary",
        "muscles.glb": "model/gltf-binary",
        "nerves.glb": "model/gltf-binary",
        "bones.glb": "model/gltf-binary"}

def main():
    global ASSETS
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "standalone.html")
    if len(sys.argv) > 2:
        ASSETS = sys.argv[2]
    s = open(APP, encoding="utf-8").read()
    embedded = {}
    for name, mime in MIME.items():
        path = os.path.join(ASSETS, name)
        if not os.path.exists(path):
            sys.exit("missing %s -- run make_assets.py first" % path)
        with open(path, "rb") as f:
            embedded[name] = "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode("ascii"))
    blob = ("<!-- Anatomy assets embedded as data URIs so this file needs nothing beside it.\n"
            "     BodyParts3D, (c) The Database Center for Life Science, CC BY-SA 2.1 Japan. -->\n"
            "<script>window.PAIN_LOCATOR_ASSET_MAP=" + json.dumps(embedded) + ";</script>\n")
    anchor = "<!-- three.js r128 GLTFLoader"
    if anchor not in s:
        sys.exit("anchor comment not found in index.html; the build needs updating")
    open(out, "w", encoding="utf-8").write(s.replace(anchor, blob + anchor, 1))
    print("wrote %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))

if __name__ == "__main__":
    main()
