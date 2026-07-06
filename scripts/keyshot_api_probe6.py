# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 PROBE 6 - force a unique material copy via temp-swap
# Hypothesis: link=False duplicates only on a genuine CHANGE. So swap the
# fixture to a throwaway material, then assign the light material back with
# link=False -> should create a uniquely-named copy. Test on "Element 2".
# No rendering. Paste the [p6] output.
# ============================================================================
import lux

def log(m): print("[p6] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def mats(): return list(lux.getSceneMaterials())

n = find("Element 2")
before = mats()
log("Element 2 material=%r ; count=%d" % (n.getMaterial(), len(before)))

# 1) swap to a throwaway existing material (linked)
try:
    n.setMaterial("Ceiling Spotlight - Glass", link=True)
    log("after temp swap, material = %r" % n.getMaterial())
except Exception as e:
    log("temp swap err: %s" % e)

# 2) assign the light material back, as a CHANGE, with link=False (duplicate)
try:
    n.setMaterial("Ceiling Spotlight", link=False)
except Exception as e:
    log("reassign err: %s" % e)

after = mats()
new = [m for m in after if m not in before]
log("count AFTER=%d ; NEW material names = %s" % (len(after), new))
log("Element 2 getMaterial() now = %r" % n.getMaterial())

# confirm the new material is a working light (has a power node)
mat = n.getMaterial()
g = lux.getMaterialGraph(mat)
haspow = []
for sn in g.getNodes():
    try:
        p = sn.getParameter("power")
        if p is not None and isinstance(p.getValue(),(int,float)):
            haspow.append((sn.getID(), p.getValue()))
    except Exception:
        pass
log("new material %r emitter power nodes = %s" % (mat, haspow))
log("(Element 2 is left on its new material; run reset_scene.py later to tidy.)")
log("================ END PROBE 6 ================")
