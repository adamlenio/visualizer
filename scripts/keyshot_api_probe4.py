# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 API PROBE 4 - material duplication / per-mesh assignment
# Goal: give each of the 13 light meshes its OWN independent material so each
# luminaire can be powered/coloured on its own. No rendering. Paste output.
# ============================================================================
import lux

def log(m): print("[probe4] " + str(m))
def filt(names, keys):
    return sorted([n for n in names if any(k.lower() in n.lower() for k in keys)])

ln = dir(lux)
log("copy/dup/unlink : " + str(filt(ln, ["copy","duplicate","unlink","instance","clone"])))
log("material funcs  : " + str(filt(ln, ["material"])))

for name in ["createSceneMaterial","getObjectMaterial","setObjectMaterial",
             "getMaterialGraph","saveMaterial","importMaterials","loadMaterials",
             "applyMaterialMapping","getSceneMaterials"]:
    fn=getattr(lux,name,None)
    if fn:
        log("==== help(lux.%s) ===="%name)
        try: help(fn)
        except Exception as e: log("help err: "+str(e))
    else:
        log("lux.%s : NOT PRESENT"%name)

# SceneNode.setMaterial signature
tree=lux.getSceneTree()
def find(n):
    r=tree.find(n); return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
node=find("Linear Light 1")
log("==== node methods (material) ==== " + str(filt(dir(node),["material"])))
for m in ["setMaterial","getMaterial"]:
    fn=getattr(node,m,None)
    if fn:
        log("---- help(SceneNode.%s) ----"%m)
        try: help(fn)
        except Exception as e: log("help err: "+str(e))

# current materials in scene
try:
    log("scene materials: " + str(lux.getSceneMaterials()))
except Exception as e:
    log("getSceneMaterials err: "+str(e))

# MaterialGraph methods that might create/copy
g=lux.getMaterialGraph(node.getMaterial())
log("MaterialGraph methods: " + str([m for m in dir(g) if not m.startswith('__')]))
log("================ END PROBE 4 ================")
