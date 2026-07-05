# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - NETWORK STATE-CAPTURE DIAGNOSTIC (2 jobs only)
# Question: does setSendToNetwork(True) capture per-call scene state, or does
# it package one shared state (the async bug we saw)?
#
# Two DELIBERATELY different + bright passes are submitted to the FARM:
#   A: linears, warm (2700K-ish), 20000 lm
#   B: ceiling, violet gel, 8000 lm
# Environment left ON (normal) so both are obviously lit; output PNG so you can
# eyeball the two thumbnails in the Network Monitor without any tooling.
#
# NO queue, NO state-restore (so nothing can overwrite state before packaging).
#
# RESULT TO REPORT:
#   * Do the two jobs appear in the NETWORK MONITOR (not local render)?
#   * Do the two thumbnails look DIFFERENT (warm room vs violet room)?
# If different -> setSendToNetwork captures per-call; we build the real script
#   on it. If identical -> we switch to saving per-pass scene packages.
# ============================================================================
import lux, os, datetime

CAMERA_NAME = "hero"
RES_W, RES_H = 1280, 800
OUT = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders/2026-07-05_network-diagnostic"

PASSES = [
    {"members": ["Linear Light 1", "Linear Light 2", "Linear Light 3"],
     "all_off": ["Element 1","Element 2","Element 3","Element 4","Element 5",
                 "Element 6","Element 7","Element 8","Conference 1","Conference 2"],
     "color": (1.0, 0.64, 0.33), "power": 20000.0, "name": "A_linears_warm"},
    {"members": ["Element 1","Element 2","Element 3","Element 4","Element 5",
                 "Element 6","Element 7","Element 8","Conference 1","Conference 2"],
     "all_off": ["Linear Light 1", "Linear Light 2", "Linear Light 3"],
     "color": (0.42, 0.20, 1.0), "power": 8000.0, "name": "B_ceiling_violet"},
]

def log(m): print("[nettest] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def set_hidden(name, hidden):
    n = find(name)
    if n:
        try: n.hide(hidden)
        except Exception:
            if n.isHidden() != hidden: n.hide()
def safe_param(node, nm):
    try: return node.getParameter(nm)
    except Exception: return None
def light_shader(mat):
    g = lux.getMaterialGraph(mat); best=bp=None
    for sn in g.getNodes():
        p = safe_param(sn,"power")
        if p is None: continue
        try: v = p.getValue()
        except Exception: v=None
        if isinstance(v,(int,float)) and (bp is None or v>bp): bp,best=v,sn
    return best

if not os.path.isdir(OUT): os.makedirs(OUT)
log("Output: " + OUT)

for spec in PASSES:
    log("Configuring pass " + spec["name"])
    for n in spec["all_off"]: set_hidden(n, True)
    for n in spec["members"]: set_hidden(n, False)
    mat = find(spec["members"][0]).getMaterial()
    sh = light_shader(mat)
    safe_param(sh,"color").setValue(tuple(spec["color"]))
    safe_param(sh,"power").setValue(spec["power"])
    log("  material={0} color={1} power={2}".format(mat, spec["color"], spec["power"]))

    lux.setCamera(CAMERA_NAME)
    opts = lux.getRenderOptions()
    opts.setMaxSamplesRendering(64)         # low - just a diagnostic
    opts.setSendToNetwork(True)             # FARM, no queue
    path = os.path.join(OUT, spec["name"] + ".png")
    lux.renderImage(path, width=RES_W, height=RES_H, opts=opts, format=lux.RENDER_OUTPUT_PNG)
    log("  submitted -> " + path)

log("Done. Check the Network Monitor: 2 jobs, and are the thumbnails different?")
