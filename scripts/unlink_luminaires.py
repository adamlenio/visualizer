# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 - UNLINK LUMINAIRES (one material per fixture)
# The 13 light fixtures currently share 2 materials (Office Light / Ceiling
# Spotlight), so they can only be controlled as 2 groups. This gives each
# fixture its OWN material via setMaterial(link=False), which duplicates it.
# After this, each luminaire can be powered/coloured individually.
#
# Run ONCE, verify the printout shows 13 UNIQUE material names, then File > Save
# so the independent materials persist in the scene.
# ============================================================================
import lux

def log(m): print("[unlink] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r

LUMINAIRES = [
    "Linear Light 1", "Linear Light 2", "Linear Light 3",
    "Element 1", "Element 2", "Element 3", "Element 4",
    "Element 5", "Element 6", "Element 7", "Element 8",
    "Conference 1", "Conference 2",
]

log("Before: shared materials")
for m in LUMINAIRES:
    n = find(m)
    log("  %-16s -> %r" % (m, n.getMaterial() if n else "MISSING"))

log("Unlinking (setMaterial link=False duplicates)...")
mapping = {}
for m in LUMINAIRES:
    n = find(m)
    if n is None:
        log("  !! missing " + m); continue
    cur = n.getMaterial()
    try:
        n.setMaterial(cur, link=False)   # duplicate -> independent copy
    except Exception as e:
        log("  setMaterial failed for %s: %s" % (m, e)); continue
    mapping[m] = n.getMaterial()

log("After: each fixture's material")
for m in LUMINAIRES:
    log("  %-16s -> %r" % (m, mapping.get(m, "?")))

names = list(mapping.values())
uniq = set(names)
log("==== %d fixtures, %d unique materials ====" % (len(names), len(uniq)))
if len(uniq) == len(LUMINAIRES):
    log("SUCCESS: every fixture has its own material. Now File > Save.")
else:
    log("PROBLEM: some materials are still shared -> " +
        str([n for n in names if names.count(n) > 1]))
    log("Paste this log back to Claude before saving.")
