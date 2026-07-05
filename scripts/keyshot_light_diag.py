# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - LIGHT-OFF DIAGNOSTIC (single local render)
# Why do the linear-light passes render black? This gathers facts + renders ONE
# viewable image locally. Paste the [diag] output AND upload the PNG.
#
#   * Prints isHidden() of each linear mesh AFTER isolation (are they visible?)
#   * Dumps the "Office Light" material graph: node ids/types/names/power, and
#     multi-material / sub-material info (are we lighting the inactive one?)
#   * Sets a BRIGHT warm value on EVERY area-light node in the graph
#   * Renders one image with the ENVIRONMENT ON (so the room is visible even if
#     the linear lights fail) -> look for warm glow on the ceiling linears.
# ============================================================================
import lux, os

CAMERA_NAME = "hero"
OUT = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders/2026-07-05_diag"
LINEARS = ["Linear Light 1", "Linear Light 2", "Linear Light 3"]
OTHERS  = ["Element 1","Element 2","Element 3","Element 4","Element 5",
           "Element 6","Element 7","Element 8","Conference 1","Conference 2"]

def log(m): print("[diag] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def set_hidden(name, hidden):
    n = find(name)
    if n is None: log("  missing: "+name); return
    try: n.hide(hidden)
    except Exception as e: log("  hide('%s',%s) err: %s"%(name,hidden,e))
def safe_param(node, nm):
    try: return node.getParameter(nm)
    except Exception: return None

if not os.path.isdir(OUT): os.makedirs(OUT)

# 1) isolate linears
log("Isolating linears (show 1-3, hide others)...")
for n in OTHERS:  set_hidden(n, True)
for n in LINEARS: set_hidden(n, False)

# 2) report visibility state after isolation
log("---- visibility after isolate ----")
for n in LINEARS + OTHERS[:3]:
    node = find(n)
    try: log("  %-16s isHidden=%s"%(n, node.isHidden()))
    except Exception as e: log("  %-16s isHidden? err %s"%(n,e))

# 3) dump Office Light graph
mat = find("Linear Light 1").getMaterial()
log("Linear Light 1 material = %r"%mat)
graph = lux.getMaterialGraph(mat)
log("---- graph nodes ----")
area_nodes = []
for sn in graph.getNodes():
    t = sn.getType()
    p = safe_param(sn, "power")
    pw = None
    if p:
        try: pw = p.getValue()
        except Exception: pw = "?"
    log("  id=%s type=%s name=%r power=%s"%(sn.getID(), t.get('name') if isinstance(t,dict) else t, sn.getName(), pw))
    if p is not None: area_nodes.append(sn)
# multi-material / current sub-material info
for meth in ["getMultiMaterial", "getRoot"]:
    fn = getattr(graph, meth, None)
    if fn:
        try: log("  graph.%s() -> %s"%(meth, fn()))
        except Exception as e: log("  graph.%s() err: %s"%(meth,e))

# 4) set BRIGHT warm on EVERY area-light node (belt & suspenders)
log("Setting power=60000 warm on all %d area-light nodes..."%len(area_nodes))
for sn in area_nodes:
    c = safe_param(sn,"color"); pw = safe_param(sn,"power")
    if c:  c.setValue((1.0,0.62,0.30))
    if pw: pw.setValue(60000.0)
# read back
for sn in area_nodes:
    pw = safe_param(sn,"power")
    log("  id=%s power now=%s"%(sn.getID(), pw.getValue() if pw else "n/a"))

# 5) render ONE image locally with ENV ON so room is visible
lux.setCamera(CAMERA_NAME)
opts = lux.getRenderOptions()
try: opts.setMaxSamplesRendering(48)
except Exception: pass
path = os.path.join(OUT, "diag_linears_envON.png")
log("Rendering (local, blocking) -> " + path)
lux.renderImage(path, width=1280, height=800, opts=opts, format=lux.RENDER_OUTPUT_PNG)
log("DONE. Upload the PNG and paste this whole [diag] log.")
