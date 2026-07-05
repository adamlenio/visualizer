# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - FARM RE-TEST (power-only isolation, 2 jobs to the network)
# Now that lights isolate correctly by POWER, retest whether the render farm
# captures per-pass state. Earlier "identical" farm results were confounded by
# the visibility bug (lights never turned on).
#
# PREREQ: the 13 light meshes must be UNHIDDEN (same as the main script).
#
# Two obviously different jobs, env left DIM so the room is visible:
#   A: linears RED 5,000,000 lm, ceiling 0
#   B: linears 0,               ceiling GREEN 5,000,000 lm
# setSendToNetwork(True), NO queue, NO restore (scene ends at B's state).
#
# READ THE RESULT:
#   * Do 2 jobs appear in the Network Monitor?
#   * Is A clearly RED and B clearly GREEN (different)?  -> farm captures
#     per-pass state; we switch the main script back to the farm.
#   * Both look the SAME (e.g. both green)?  -> farm defers packaging to script
#     end; stay on the local queue.
# ============================================================================
import lux, os

CAMERA_NAME = "hero"
OUT = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders/2026-07-05_farm-retest"

def log(m): print("[farm] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def safe_param(node,nm):
    try: return node.getParameter(nm)
    except Exception: return None
def power_nodes(mat):
    g=lux.getMaterialGraph(mat); out=[]
    for sn in g.getNodes():
        p=safe_param(sn,"power")
        if p is None: continue
        try:
            if isinstance(p.getValue(),(int,float)): out.append(sn)
        except Exception: pass
    return out
def set_material(mat, lumens, color=None):
    for sn in power_nodes(mat):
        p=safe_param(sn,"power")
        if p: p.setValue(float(lumens))
        if color is not None:
            c=safe_param(sn,"color")
            if c: c.setValue(tuple(color))

if not os.path.isdir(OUT): os.makedirs(OUT)
office = find("Linear Light 1").getMaterial()
ceil   = find("Element 1").getMaterial()
env = lux.getActiveEnvironment(); env.setBrightness(0.2)

def submit(name, off_l, off_rgb, cei_l, cei_rgb):
    set_material(office, off_l, off_rgb)
    set_material(ceil,   cei_l, cei_rgb)
    lux.setCamera(CAMERA_NAME)
    opts = lux.getRenderOptions()
    try: opts.setMaxSamplesRendering(48)
    except Exception: pass
    opts.setSendToNetwork(True)          # FARM, no queue
    path = os.path.join(OUT, name + ".png")
    lux.renderImage(path, width=1280, height=800, opts=opts, format=lux.RENDER_OUTPUT_PNG)
    log("submitted %s -> %s"%(name, path))

submit("A_linears_RED",  5000000, (1.0,0.0,0.0), 0, None)
submit("B_ceiling_GREEN", 0, None, 5000000, (0.0,1.0,0.0))
log("Done. Check Network Monitor: 2 jobs. Is A red and B green (different)?")
