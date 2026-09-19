import bpy, json
from mathutils import Vector
KEEP = ["Spinal dura", "Spinal ganglion.l", "Spinal ganglion.r"]
OUT = "/tmp/claude-0/-home-user--github/20bbad1b-a78a-5d06-a82a-1af56adfb6b1/scratchpad/za_ns_raw.obj"

def bb(objs):
    lo=[1e9]*3; hi=[-1e9]*3
    for o in objs:
        for c in o.bound_box:
            w=o.matrix_world @ Vector(c)
            for i in range(3):
                lo[i]=min(lo[i],w[i]); hi[i]=max(hi[i],w[i])
    return lo,hi

# vertebrae only: a central structure both datasets share, free of stray outliers
verts=[o for o in bpy.data.objects if o.type=='MESH' and len(o.data.vertices)>200
       and ('vertebra' in o.name.lower() or o.name.lower().startswith(('c1 ','c2 ','t1 ','l1 ')))]
lo,hi = bb(verts)
print("ZA_VERT " + json.dumps({"n":len(verts),
      "yup_min":[lo[0],lo[2],-hi[1]], "yup_max":[hi[0],hi[2],-lo[1]]}))

bpy.ops.object.select_all(action='DESELECT')
got=[]
for nm in KEEP:
    o=bpy.data.objects.get(nm)
    if not o: continue
    o.hide_set(False); o.hide_viewport=False; o.hide_render=False
    o.select_set(True); got.append(nm)
bpy.context.view_layer.objects.active=bpy.data.objects.get(KEEP[0])
print("EXPORTING", got)
bpy.ops.wm.obj_export(filepath=OUT, export_selected_objects=True,
                      export_materials=False, export_normals=True,
                      forward_axis='NEGATIVE_Z', up_axis='Y')
print("DONE")
