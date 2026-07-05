# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 (15.1) API PROBE 2 - graph / options / env / image style
# Run in Scripting Console, paste the WHOLE output back to Claude.
# No rendering. This pins the last calls needed to finalize the render script.
# ============================================================================
import lux

def log(m): print("[probe2] " + str(m))
def names(o): return sorted([n for n in dir(o) if not n.startswith("__")])

tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    if isinstance(r, (list, tuple)):
        return r[0] if r else None
    return r

# ---- MATERIAL GRAPH + MESH-LIGHT SHADER NODE -------------------------------
log("================ MATERIAL GRAPH ================")
mat_name = find("Linear Light 1").getMaterial()   # -> "Office Light"
log("material name: " + repr(mat_name))
graph = lux.getMaterialGraph(mat_name)
log("graph type: " + str(type(graph)))
log("graph methods: " + str(names(graph)))

# try to enumerate shader nodes
shader_nodes = None
for getter in ["getNodes", "getShaderNodes", "getChildren", "getRoot"]:
    fn = getattr(graph, getter, None)
    if fn:
        try:
            val = fn()
            log("graph.{0}() -> type={1} value={2}".format(getter, type(val), val))
            if getter in ("getNodes", "getShaderNodes") and val:
                shader_nodes = val
        except Exception as e:
            log("graph.{0}() FAILED: {1}".format(getter, e))

# inspect each shader node's parameters
def dump_shader(node, label=""):
    log("---- shader node {0}: {1} ----".format(label, node))
    log("  methods: " + str(names(node)))
    for getter in ["getName", "getType", "getShaderType"]:
        fn = getattr(node, getter, None)
        if fn:
            try: log("  {0}() -> {1}".format(getter, fn()))
            except Exception as e: log("  {0}() FAILED: {1}".format(getter, e))
    # parameters
    for pg in ["getParameters", "getParameterNames", "getInputs"]:
        fn = getattr(node, pg, None)
        if fn:
            try:
                params = fn()
                log("  {0}() -> {1}".format(pg, params))
                # if list of param objects, dump name+value
                if isinstance(params, (list, tuple)):
                    for p in params:
                        nm = getattr(p, "getName", lambda: p)()
                        try: val = p.getValue()
                        except Exception: val = "<no getValue>"
                        log("      param name={0!r} value={1}".format(nm, val))
            except Exception as e:
                log("  {0}() FAILED: {1}".format(pg, e))

try:
    if shader_nodes:
        # shader_nodes may be a dict or list
        seq = shader_nodes.values() if hasattr(shader_nodes, "values") else shader_nodes
        for i, sn in enumerate(seq):
            dump_shader(sn, str(i))
    else:
        root = graph.getRoot() if hasattr(graph, "getRoot") else None
        if root: dump_shader(root, "root")
except Exception as e:
    log("shader enumeration failed: " + str(e))

# ---- RENDER OPTIONS (network / samples / output / exposure) ----------------
log("================ RENDER OPTIONS ================")
opts = lux.getRenderOptions()
log("opts type: " + str(type(opts)))
log("opts methods: " + str(names(opts)))

# ---- ENVIRONMENT -----------------------------------------------------------
log("================ ENVIRONMENT ================")
try:
    env = lux.getActiveEnvironment()
    log("active env type: " + str(type(env)))
    log("env methods: " + str(names(env)))
except Exception as e:
    log("getActiveEnvironment failed: " + str(e))

# ---- IMAGE STYLE (exposure lives here in KS2026) ---------------------------
log("================ IMAGE STYLE ================")
try:
    style = lux.getActiveImageStyle()
    log("active image style type: " + str(type(style)))
    log("style methods: " + str(names(style)))
except Exception as e:
    log("getActiveImageStyle failed: " + str(e))

# ---- CAMERA SETTER + NODE HIDE ---------------------------------------------
log("================ MISC ================")
for cand in ["setCamera", "setActiveCamera", "getCamera"]:
    log("lux.{0} present? {1}".format(cand, hasattr(lux, cand)))
node = find("Element 1")
log("Element 1 hide/isHidden present? hide={0} isHidden={1} getHidden={2}".format(
    hasattr(node, "hide"), hasattr(node, "isHidden"), hasattr(node, "getHidden")))
log("================ END PROBE 2 ================")
