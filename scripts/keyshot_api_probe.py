# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 (15.1) API PROBE - no rendering, just discovery
# Run in Scripting Console, then paste the WHOLE output back to Claude.
# Goal: find the KS2026 calls for material/light access, colour/power,
# environment brightness, image exposure, and network submit.
# ============================================================================
import lux

def log(m): print("[probe] " + str(m))

def filt(names, keys):
    return sorted([n for n in names if any(k.lower() in n.lower() for k in keys)])

log("================ lux module surface ================")
lux_names = dir(lux)
log("lux has {0} attributes".format(len(lux_names)))
log("material : " + str(filt(lux_names, ["material", "graph"])))
log("light    : " + str(filt(lux_names, ["light"])))
log("color    : " + str(filt(lux_names, ["color", "colour", "temperature", "kelvin"])))
log("power    : " + str(filt(lux_names, ["power", "lumen", "intensity", "watt"])))
log("env      : " + str(filt(lux_names, ["environment", "env", "hdri", "brightness"])))
log("exposure : " + str(filt(lux_names, ["exposure", "tonemap", "image"])))
log("network  : " + str(filt(lux_names, ["network", "queue", "submit", "render"])))
log("scene    : " + str(filt(lux_names, ["scene", "tree", "node", "getcam"])))

log("================ scene tree node API ================")
tree = lux.getSceneTree()
log("tree type: " + str(type(tree)))
log("tree dir : " + str(filt(dir(tree), ["find", "root", "child", "node", "get"])))

def probe_node(name):
    log("---- node: {0!r} ----".format(name))
    r = tree.find(name)
    log("  find() -> type={0} value={1}".format(type(r), r))
    node = r[0] if isinstance(r, (list, tuple)) and r else r
    if node is None:
        log("  (not found)")
        return
    # methods that look relevant
    d = dir(node)
    log("  node methods (material/light/color/power/hidden/vis): " +
        str(filt(d, ["material", "light", "color", "colour", "power",
                     "temperature", "hidden", "visib", "name", "type", "id"])))
    # try common accessors, each guarded
    for call in ["getName", "getType", "getId", "getMaterialName",
                 "getMaterial", "getMaterialGraph", "isLight", "getPower"]:
        try:
            fn = getattr(node, call, None)
            if fn:
                log("  {0}() -> {1}".format(call, fn()))
        except Exception as e:
            log("  {0}() FAILED: {1}".format(call, e))

# A mesh that carries the Office Light emissive, and the two light names
probe_node("Linear Light 1")
probe_node("Office Light")
probe_node("Ceiling Spotlight")

log("================ lux.getLights (if present) ================")
try:
    lights = lux.getLights()
    log("getLights() -> " + str(lights))
except Exception as e:
    log("getLights not available: " + str(e))

log("================ material graph attempt ================")
# If there's a module-level graph getter, show what it wants
for cand in ["getMaterialGraph", "getSceneMaterials", "getMaterials"]:
    fn = getattr(lux, cand, None)
    log("lux.{0} present? {1}".format(cand, bool(fn)))

log("================ END PROBE ================")
