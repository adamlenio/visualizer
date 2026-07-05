# -*- coding: utf-8 -*-
# ============================================================================
# Casambi Visualizer - LIGHTING CONTRAST/HUE TEST
# KeyShot 2026.2.0 (15.1.0.115) - lux scripting API (KS2026)
# Target: Network Render Farm (KeyShot Network Monitor)
# ============================================================================
#
# PURPOSE
#   Small test matrix to fix the flat look - not enough contrast in tone
#   (brightness) or hue (colour separation). NOT the full production run.
#   Renders two light groups several ways each + a base pass, all as EXR with
#   alpha, submitted to the farm.
#
# SCENE FACTS confirmed by API probes (2026-07-05):
#   * Lights are GROUP nodes; the emissive lives in the material graph of the
#     member meshes:
#       zone "linears" -> meshes "Linear Light 1..3", material "Office Light"
#                         (Area Light shader, power 20000 lm)
#       zone "ceiling" -> meshes "Element 1..8","Conference 1..2"
#                         (Ceiling Spotlight material)
#   * Area Light shader params: "color" (RGB tuple), "power" (float, lumens),
#     "lumen" (int unit flag = 1). NO colour-temperature param -> we set CCT as
#     RGB directly.
#   * node.getMaterial() -> material NAME (string); lux.getMaterialGraph(name)
#     -> MaterialGraph; graph.getNodes() -> tuple of ShaderNode; the active
#     emissive node is the one with the highest "power" value (KS14 heuristic,
#     still holds - two Area Light nodes exist, 0 lm and 20000 lm).
#   * Visibility: node.hide(bool) / node.isHidden().
#   * Environment: lux.getActiveEnvironment() -> Env; env.setBrightness(v).
#   * Exposure: saved in the scene Image Style at 1 EV. We DO NOT touch it, so
#     every pass shares identical tone mapping (required for additive compose).
#   * Network: opts.setSendToNetwork(True). Alpha: opts.setOutputAlphaChannel.
#   * Camera: lux.setCamera(name) (run before EVERY render - KS14 drift bug).
#
# COMPOSITING SETUP
#   Base pass: HDRI on (original brightness), all lights off -> ambient room.
#   Light passes: env brightness -> ~0 so each pass is one light on black.
#   This keeps ambient from being added once per layer in the compositor.
#
# HOW TO RUN
#   1. Confirm CAMERA_NAME below (valid names in this scene: hero, Front, Back,
#      Rest Space, Meeting Room, Desk, Flat).
#   2. FIRST leave SUBMIT = False -> INSPECTION ONLY. It prints the renderImage
#      signature, confirms setValue, and shows the light node it will drive per
#      zone. Paste that back to me.
#   3. Then set SUBMIT = True and run again to push the passes to the farm.
# ============================================================================

import lux
import os

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
SUBMIT        = False
CAMERA_NAME   = "hero"
OUTPUT_DIR    = os.path.expanduser("~/Casambi_Renders/office/lighting_test")
RES_W         = 1920
RES_H         = 1200
SAMPLES       = 128
FORMAT_EXR    = True

BLACKOUT_ENV_FOR_LIGHT_PASSES = True
ENV_BLACK_BRIGHTNESS = 0.0001    # KS minimum is 0.0001, not 0.0

# Kelvin -> approximate sRGB light colour (max channel ~1.0). Tune from EXRs.
KELVIN_RGB = {
    2400: (1.00, 0.56, 0.25),
    2700: (1.00, 0.64, 0.33),
    3000: (1.00, 0.70, 0.42),
    6500: (1.00, 0.99, 0.97),
}

# Zones: material name is DERIVED from the first member mesh at runtime.
ZONES = {
    "linears": {"members": ["Linear Light 1", "Linear Light 2", "Linear Light 3"]},
    "ceiling": {"members": ["Element 1", "Element 2", "Element 3", "Element 4",
                            "Element 5", "Element 6", "Element 7", "Element 8",
                            "Conference 1", "Conference 2"]},
}

# Test matrix. "kelvin" -> colour via KELVIN_RGB; "rgb" -> direct gel.
TEST_MATRIX = [
    # linears (Office Light, base 20000 lm): tone / contrast
    {"zone": "linears", "tag": "v1_2700_20k", "kelvin": 2700, "lumens": 20000},
    {"zone": "linears", "tag": "v2_2400_20k", "kelvin": 2400, "lumens": 20000},
    {"zone": "linears", "tag": "v3_2700_30k", "kelvin": 2700, "lumens": 30000},
    {"zone": "linears", "tag": "v4_6500_20k", "kelvin": 6500, "lumens": 20000},
    # ceiling (Ceiling Spotlight, base 5000 lm): hue
    {"zone": "ceiling", "tag": "v1_2700_5k",  "kelvin": 2700, "lumens": 5000},
    {"zone": "ceiling", "tag": "v2_6500_5k",  "kelvin": 6500, "lumens": 5000},
    {"zone": "ceiling", "tag": "v3_violet_5k","rgb": (0.42, 0.20, 1.0), "lumens": 5000},
    {"zone": "ceiling", "tag": "v4_violet_8k","rgb": (0.42, 0.20, 1.0), "lumens": 8000},
]

# ============================================================================
# HELPERS
# ============================================================================
def log(m): print("[lighting_test] " + str(m))
def ext(): return "exr" if FORMAT_EXR else "png"

def ensure_output_dir():
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    log("Output dir: " + OUTPUT_DIR)

_tree = None
def tree():
    global _tree
    if _tree is None:
        _tree = lux.getSceneTree()
    return _tree

def find(name):
    r = tree().find(name)
    if isinstance(r, (list, tuple)):
        return r[0] if r else None
    return r

def all_member_names():
    out = []
    for z in ZONES.values():
        out.extend(z["members"])
    return out

def set_hidden(name, hidden):
    node = find(name)
    if node is None:
        log("  !! mesh not found: " + name); return
    try:
        node.hide(hidden)
    except Exception:
        try:
            if node.isHidden() != hidden:
                node.hide()
        except Exception as e:
            log("  hide failed for {0}: {1}".format(name, e))

def hide_all_members():
    for n in all_member_names():
        set_hidden(n, True)

def isolate_zone(zk):
    hide_all_members()
    for n in ZONES[zk]["members"]:
        set_hidden(n, False)

# --- Light shader access -----------------------------------------------------
def zone_material_name(zk):
    first = ZONES[zk]["members"][0]
    node = find(first)
    return node.getMaterial() if node else None

def safe_param(node, name):
    """getParameter() RAISES for names not on the node -> guard it."""
    try:
        return node.getParameter(name)
    except Exception:
        return None

def light_shader_of(material_name):
    """Return the emissive ShaderNode = the one carrying the highest 'power'
    value (works for Area Light and Spotlight alike)."""
    graph = lux.getMaterialGraph(material_name)
    best, best_p = None, None
    for sn in graph.getNodes():
        p = safe_param(sn, "power")
        if p is None:
            continue
        try:
            v = p.getValue()
        except Exception:
            v = None
        if isinstance(v, (int, float)):
            if best_p is None or v > best_p:
                best_p, best = v, sn
    return best

def set_param(node, name, value):
    p = safe_param(node, name)
    if p is None:
        log("  !! param '{0}' not on node".format(name)); return False
    try:
        p.setValue(value)
        return True
    except Exception as e:
        log("  setValue('{0}') failed: {1}".format(name, e)); return False

def apply_light_spec(zk, spec):
    mat = zone_material_name(zk)
    if not mat:
        log("  !! no material for zone " + zk); return False
    shader = light_shader_of(mat)
    if shader is None:
        log("  !! no light shader found in material " + mat); return False
    color = spec["rgb"] if "rgb" in spec else KELVIN_RGB[spec["kelvin"]]
    set_param(shader, "color", tuple(color))
    set_param(shader, "power", float(spec["lumens"]))
    log("  {0}: colour={1} power={2}lm".format(mat, tuple(round(c,3) for c in color), spec["lumens"]))
    return True

def snapshot_zone(zk):
    """Capture current colour+power so we can restore after the test."""
    mat = zone_material_name(zk)
    shader = light_shader_of(mat) if mat else None
    if shader is None:
        return None
    try:
        return (mat, shader.getParameter("color").getValue(),
                shader.getParameter("power").getValue())
    except Exception:
        return None

def restore_zone(snap):
    if not snap:
        return
    mat, color, power = snap
    shader = light_shader_of(mat)
    if shader:
        set_param(shader, "color", color)
        set_param(shader, "power", power)

# --- Environment -------------------------------------------------------------
def get_env():
    try:
        return lux.getActiveEnvironment()
    except Exception as e:
        log("  getActiveEnvironment failed: " + str(e)); return None

def set_env_brightness(v):
    env = get_env()
    if env:
        try: env.setBrightness(v)
        except Exception as e: log("  setBrightness failed: " + str(e))

# --- Render ------------------------------------------------------------------
def render_options():
    opts = lux.getRenderOptions()
    for setter, arg in [("setMaxSamplesRendering", SAMPLES),
                        ("setOutputAlphaChannel", True),
                        ("setSendToNetwork", True),
                        ("setOutputRenderLayers", False)]:
        fn = getattr(opts, setter, None)
        if fn:
            try: fn(arg)
            except Exception as e: log("  {0} failed: {1}".format(setter, e))
    return opts

def submit_pass(path):
    lux.setCamera(CAMERA_NAME)   # before EVERY render
    opts = render_options()
    fmt = lux.RENDER_OUTPUT_EXR if FORMAT_EXR else lux.RENDER_OUTPUT_PNG
    # renderImage signature confirmed in inspect(); with setSendToNetwork the
    # call submits to the farm rather than rendering locally.
    lux.renderImage(path, width=RES_W, height=RES_H, opts=opts, renderOutput=fmt)
    log("  submitted -> " + path)

# ============================================================================
# PHASES
# ============================================================================
def inspect():
    log("================ INSPECTION (no rendering) ================")
    log("Cameras: " + str(lux.getCameras()))
    env = get_env()
    if env:
        log("Active env: {0}  brightness={1}".format(env.getName(), env.getBrightness()))
    for zk in ZONES:
        mat = zone_material_name(zk)
        shader = light_shader_of(mat) if mat else None
        log("zone '{0}': material={1!r}".format(zk, mat))
        if shader:
            log("   light node id={0} color={1} power={2}".format(
                shader.getID(),
                shader.getParameter("color").getValue(),
                shader.getParameter("power").getValue()))
            # confirm setValue exists on a ShaderParameter
            p = shader.getParameter("power")
            log("   ShaderParameter has setValue? {0}".format(hasattr(p, "setValue")))
    log("---- renderImage signature ----")
    try:
        help(lux.renderImage)
    except Exception as e:
        log("help(renderImage) failed: " + str(e))
    log("================ END INSPECTION ================")
    log("If this looks right, set SUBMIT = True and run again.")

def run_matrix():
    ensure_output_dir()
    snaps = {zk: snapshot_zone(zk) for zk in ZONES}
    orig_env_brightness = get_env().getBrightness() if get_env() else 1.0
    try:
        # BASE: lights off, HDRI ambient
        log("Base pass (lights off, HDRI ambient):")
        hide_all_members()
        set_env_brightness(orig_env_brightness)
        submit_pass(os.path.join(OUTPUT_DIR, "base_off." + ext()))

        # LIGHT PASSES: env blacked out
        if BLACKOUT_ENV_FOR_LIGHT_PASSES:
            set_env_brightness(ENV_BLACK_BRIGHTNESS)

        ok = fail = 0
        for spec in TEST_MATRIX:
            tag = "{0}_{1}".format(spec["zone"], spec["tag"])
            log("Pass: " + tag)
            try:
                isolate_zone(spec["zone"])
                if not apply_light_spec(spec["zone"], spec):
                    fail += 1; continue
                submit_pass(os.path.join(OUTPUT_DIR, "light_{0}.{1}".format(tag, ext())))
                ok += 1
            except Exception as e:
                fail += 1; log("  PASS FAILED: " + str(e))
        log("==== submitted {0} passes, {1} failed ====".format(ok, fail))
    finally:
        # restore scene state
        set_env_brightness(orig_env_brightness)
        for zk in ZONES:
            restore_zone(snaps[zk])
        for n in all_member_names():
            set_hidden(n, False)
        log("Scene state restored (env brightness, light params, visibility).")

def main():
    log("KeyShot lighting test - SUBMIT={0}, format={1}".format(SUBMIT, ext()))
    if SUBMIT: run_matrix()
    else:      inspect()

main()
