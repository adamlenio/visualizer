# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - FARM BATCH RELIABILITY TEST (8 distinct passes)
# Settles whether the render farm handles a rapid multi-pass batch. Each pass
# is a UNIQUE colour on one zone (other zone off), env dim so it's visible.
# If the farm captures state per-submit, each output shows its intended colour.
# If it races, some outputs will show the wrong colour / repeat.
#
# Renders straight into the project folder so results can be checked directly
# (no re-uploading). setSendToNetwork = farm. SUBMIT_DELAY gives the farm time
# to package each job before the next state change. NO restore during the batch
# (run reset_scene.py afterwards to clean up).
#
# PREREQ: the 13 light meshes stay UNHIDDEN (as set up earlier).
# ============================================================================
import lux, os, time

CAMERA_NAME  = "hero"
OUT = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders/2026-07-05_farm-batch-test"
RES_W, RES_H = 1280, 800
SAMPLES      = 48          # low - just a reliability probe
SUBMIT_DELAY = 4.0         # seconds between farm submits (beat the async race)

def log(m): print("[farmbatch] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def safe_param(node,nm):
    try: return node.getParameter(nm)
    except Exception: return None
def set_material(mat, lumens, color=None):
    g = lux.getMaterialGraph(mat)
    for sn in g.getNodes():
        p = safe_param(sn,"power")
        if p is None: continue
        try:
            if not isinstance(p.getValue(),(int,float)): continue
        except Exception: continue
        p.setValue(float(lumens))
        if color is not None:
            c = safe_param(sn,"color")
            if c: c.setValue(tuple(color))

if not os.path.isdir(OUT): os.makedirs(OUT)
office = find("Linear Light 1").getMaterial()
ceil   = find("Element 1").getMaterial()
env = lux.getActiveEnvironment(); env.setBrightness(0.2)

# 8 passes: (name, zone, rgb).  Distinct hues -> mismatches are obvious.
PASSES = [
    ("p1_linears_RED",     "lin", (1.0, 0.0, 0.0)),
    ("p2_ceiling_GREEN",   "cei", (0.0, 1.0, 0.0)),
    ("p3_linears_BLUE",    "lin", (0.0, 0.3, 1.0)),
    ("p4_ceiling_YELLOW",  "cei", (1.0, 0.9, 0.0)),
    ("p5_linears_MAGENTA", "lin", (1.0, 0.0, 1.0)),
    ("p6_ceiling_CYAN",    "cei", (0.0, 1.0, 1.0)),
    ("p7_linears_ORANGE",  "lin", (1.0, 0.5, 0.0)),
    ("p8_ceiling_WHITE",   "cei", (1.0, 1.0, 1.0)),
]

for i,(name, zone, rgb) in enumerate(PASSES):
    if zone == "lin":
        set_material(office, 40000, rgb); set_material(ceil, 0)
    else:
        set_material(ceil, 12000, rgb); set_material(office, 0)
    lux.setCamera(CAMERA_NAME)
    opts = lux.getRenderOptions()
    try: opts.setMaxSamplesRendering(SAMPLES)
    except Exception: pass
    opts.setSendToNetwork(True)
    path = os.path.join(OUT, name + ".png")
    lux.renderImage(path, width=RES_W, height=RES_H, opts=opts, format=lux.RENDER_OUTPUT_PNG)
    log("submitted %s (%s)"%(name, rgb))
    if i < len(PASSES)-1:
        time.sleep(SUBMIT_DELAY)   # let the farm package this job first

log("All 8 submitted. Check the Network Monitor, then tell me when they finish.")
log("Files land in: " + OUT)
