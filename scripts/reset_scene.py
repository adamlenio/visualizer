# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - RESET SCENE LIGHTS TO NEUTRAL DEFAULT
# Clears the red/green (and other) colours left in the light materials by the
# earlier diagnostics, restoring a clean cool-white default so the open file
# looks normal. Run once, then File > Save to bake the clean default.
#   Office Light   -> cool white, 20000 lm
#   Ceiling Spotlight -> cool white, 5000 lm
#   Environment    -> brightness 1.0
# ============================================================================
import lux

def log(m): print("[reset] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def safe_param(node,nm):
    try: return node.getParameter(nm)
    except Exception: return None

DEFAULT_WHITE = (0.80, 0.894, 1.0)   # original cool-white the scene shipped with

def reset(mesh, lumens):
    mat = find(mesh).getMaterial()
    g = lux.getMaterialGraph(mat)
    n = 0
    for sn in g.getNodes():
        p = safe_param(sn, "power")
        if p is None: continue
        try:
            if not isinstance(p.getValue(), (int, float)): continue
        except Exception: continue
        p.setValue(float(lumens))
        c = safe_param(sn, "color")
        if c: c.setValue(DEFAULT_WHITE)
        n += 1
    log("%s (material %r): reset %d emitter node(s) -> white, %d lm" % (mesh, mat, n, lumens))

reset("Linear Light 1", 20000)   # Office Light
reset("Element 1", 5000)         # Ceiling Spotlight
try:
    env = lux.getActiveEnvironment(); env.setBrightness(1.0)
    log("env brightness -> 1.0")
except Exception as e:
    log("env reset failed: " + str(e))
log("DONE. Review the real-time view, then File > Save to keep this clean default.")
