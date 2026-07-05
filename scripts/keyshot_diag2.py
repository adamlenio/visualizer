# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - DIAG 2: does a material-graph power edit actually change the
# render, and what is each light's current visibility?
# Env left DIM (0.2) so the room is always visible. We push EXTREME colours so
# any working light is unmistakable:
#     Office Light (linears)  -> power 5,000,000  RED
#     Ceiling Spotlight       -> power 5,000,000  GREEN
# We do NOT change visibility here - this tests only whether already-visible
# lights respond to graph edits. Element 8 is visible by default, so if the
# ceiling responds we should see GREEN near it.
# Paste the [d2] log AND upload the PNG.
# ============================================================================
import lux, os

CAMERA_NAME = "hero"
OUT = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders/2026-07-05_diag2"
LINEARS = ["Linear Light 1","Linear Light 2","Linear Light 3"]
CEILING = ["Element 1","Element 2","Element 3","Element 4","Element 5",
           "Element 6","Element 7","Element 8","Conference 1","Conference 2"]

def log(m): print("[d2] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def safe_param(node,nm):
    try: return node.getParameter(nm)
    except Exception: return None

if not os.path.isdir(OUT): os.makedirs(OUT)

# 1) current visibility of every interior light mesh
log("---- current isHidden() state ----")
for n in LINEARS + CEILING:
    node = find(n)
    try: log("  %-16s isHidden=%s"%(n, node.isHidden()))
    except Exception as e: log("  %-16s err %s"%(n,e))

# 1b) does hide() toggle? read, toggle, read, toggle, read on Linear Light 1
n0 = find("Linear Light 1")
log("hide() toggle test on 'Linear Light 1':")
log("  read1 isHidden=%s"%n0.isHidden())
n0.hide(); log("  after hide() read2 isHidden=%s"%n0.isHidden())
n0.hide(); log("  after hide() read3 isHidden=%s"%n0.isHidden())

# 2) dump BOTH light material graphs
def dump(mat):
    log("---- graph '%s' ----"%mat)
    g=lux.getMaterialGraph(mat)
    for sn in g.getNodes():
        t=sn.getType(); tn=t.get('name') if isinstance(t,dict) else t
        p=safe_param(sn,"power"); pw=None
        if p:
            try: pw=p.getValue()
            except Exception: pw="?"
        log("  id=%s type=%s name=%r power=%s"%(sn.getID(), tn, sn.getName(), pw))
    return g
office = find("Linear Light 1").getMaterial()
ceil   = find("Element 1").getMaterial()
g_off = dump(office)
g_cei = dump(ceil)

# 3) push EXTREME colour+power on ALL power-nodes of each material
def force(g, rgb, power):
    for sn in g.getNodes():
        p=safe_param(sn,"power")
        if p is None: continue
        try:
            if not isinstance(p.getValue(),(int,float)): continue
        except Exception: continue
        p.setValue(float(power))
        c=safe_param(sn,"color")
        if c: c.setValue(tuple(rgb))
force(g_off, (1.0,0.0,0.0), 5000000)   # linears RED
force(g_cei, (0.0,1.0,0.0), 5000000)   # ceiling GREEN
log("forced linears=RED ceiling=GREEN at 5,000,000 lm")

# 4) env dim so room visible; render one image
env=lux.getActiveEnvironment(); orig=env.getBrightness(); env.setBrightness(0.2)
lux.setCamera(CAMERA_NAME)
opts=lux.getRenderOptions()
try: opts.setMaxSamplesRendering(48)
except Exception: pass
path=os.path.join(OUT,"diag2_red_green.png")
log("Rendering -> "+path)
lux.renderImage(path, width=1280, height=800, opts=opts, format=lux.RENDER_OUTPUT_PNG)
env.setBrightness(orig)
log("DONE. Upload PNG + paste [d2] log.")
