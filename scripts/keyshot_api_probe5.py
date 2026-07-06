# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 PROBE 5 - how to force a uniquely-named material duplicate
# Reassigning the same material was a no-op. Find what actually duplicates and
# what the copy is called / how to address it. Tests on "Element 2" only.
# No rendering. Paste the [p5] output.
# ============================================================================
import lux

def log(m): print("[p5] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r

def mats():
    return list(lux.getSceneMaterials())

n = find("Element 2")
oid = n.getID()
log("Element 2 objID=%s material=%r" % (oid, n.getMaterial()))
before = mats()
log("scene material count BEFORE = %d ; 'Ceiling Spotlight' occurrences = %d"
    % (len(before), before.count("Ceiling Spotlight")))

# does setMaterial return anything?
try:
    ret = n.setMaterial("Ceiling Spotlight", link=False)
    log("setMaterial(link=False) returned: %r" % (ret,))
except Exception as e:
    log("setMaterial err: %s" % e)

after = mats()
new_names = [m for m in after if m not in before]
log("scene material count AFTER = %d ; NEW names = %s" % (len(after), new_names))
log("Element 2 getMaterial() now = %r" % n.getMaterial())
try:
    log("getObjectMaterial(oid) = %r" % (lux.getObjectMaterial(oid),))
except Exception as e:
    log("getObjectMaterial err: %s" % e)

# try the object-ID based setter with link=False
log("---- try lux.setObjectMaterial(mat, obj, link=False) ----")
try:
    ret2 = lux.setObjectMaterial("Ceiling Spotlight", oid, link=False)
    log("setObjectMaterial returned: %r" % (ret2,))
    after2 = mats()
    log("NEW names after setObjectMaterial = %s" % [m for m in after2 if m not in after])
    log("Element 2 getMaterial() now = %r" % n.getMaterial())
except Exception as e:
    log("setObjectMaterial err: %s" % e)

# is there a rename path on the graph?
g = lux.getMaterialGraph(n.getMaterial())
log("graph.getMaterialName() = %r" % g.getMaterialName())
log("graph methods with 'name'/'set': " +
    str([m for m in dir(g) if ('name' in m.lower() or m.startswith('set'))]))
log("================ END PROBE 5 ================")
