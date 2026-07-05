# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - SINGLE-PASS CONFIRM (blocking local render, viewable PNG)
# Proves the isolated-light layer approach works now that hide() is fixed.
# Renders ONE pass: ceiling lights ONLY, violet, env blacked out.
# Expect: a dark frame with VIOLET light where the ceiling spots hit surfaces.
# Paste the [confirm] log and upload the PNG.
# ============================================================================
import lux, os

CAMERA_NAME = "hero"
OUT = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders/2026-07-05_confirm"
CEILING = ["Element 1","Element 2","Element 3","Element 4","Element 5",
           "Element 6","Element 7","Element 8","Conference 1","Conference 2"]
LINEARS = ["Linear Light 1","Linear Light 2","Linear Light 3"]

def log(m): print("[confirm] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r

def set_hidden(name, hidden):
    node = find(name)
    if node is None: log("  missing "+name); return
    try:
        if node.isHidden() != hidden:   # hide() is a no-arg TOGGLE in KS2026
            node.hide()
    except Exception as e: log("  toggle err %s: %s"%(name,e))

def safe_param(node,nm):
    try: return node.getParameter(nm)
    except Exception: return None
def light_shader(mat):
    g=lux.getMaterialGraph(mat); best=bp=None
    for sn in g.getNodes():
        p=safe_param(sn,"power")
        if p is None: continue
        try: v=p.getValue()
        except Exception: v=None
        if isinstance(v,(int,float)) and (bp is None or v>bp): bp,best=v,sn
    return best

if not os.path.isdir(OUT): os.makedirs(OUT)

# isolate ceiling
for n in LINEARS: set_hidden(n, True)
for n in CEILING: set_hidden(n, False)
still = [n for n in CEILING if find(n) and find(n).isHidden()]
log("ceiling still hidden after isolate (should be []): " + str(still))
log("linears hidden (should all be True): " + str([find(n).isHidden() for n in LINEARS]))

# violet + power on the ceiling material
mat = find("Element 1").getMaterial()
sh = light_shader(mat)
safe_param(sh,"color").setValue((0.42,0.20,1.0))
safe_param(sh,"power").setValue(8000.0)
log("material=%r color set violet, power=8000, node power now=%s"%(mat, safe_param(sh,"power").getValue()))

# env blackout
env = lux.getActiveEnvironment()
orig = env.getBrightness()
env.setBrightness(0.0001)
log("env brightness %.4f -> 0.0001"%orig)

# blocking local render (NOT queue, NOT network) -> immediate, correct state
lux.setCamera(CAMERA_NAME)
opts = lux.getRenderOptions()
try: opts.setMaxSamplesRendering(64)
except Exception: pass
path = os.path.join(OUT, "confirm_ceiling_violet.png")
log("Rendering (local, blocking) -> " + path)
lux.renderImage(path, width=1280, height=800, opts=opts, format=lux.RENDER_OUTPUT_PNG)

# restore env
env.setBrightness(orig)
log("DONE. env restored. Upload the PNG + paste this log.")
