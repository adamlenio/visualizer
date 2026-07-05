# -*- coding: utf-8 -*-
# ============================================================================
# Casambi Visualizer - LIGHTING CONTRAST/HUE TEST  (POWER-ONLY isolation)
# KeyShot 2026.2.0 (15.1.0.115) - lux scripting API
# LOCAL QUEUE (setAddToQueue + processQueue). A 9-pass FARM run proved
# setSendToNetwork is async and RACES: it lagged behind the script and captured
# the wrong state on most passes (5 of 9 came out black). The queue saves a
# scene copy to disk SYNCHRONOUSLY per pass -> race-free, correct per-pass.
# Renders locally on the native GPU. Diagnostics also proved:
#   * Material-graph power/colour edits apply reliably and persist.
#   * hide()/visibility is unreliable on these Group light nodes -> DO NOT USE.
# So we isolate lights by POWER only: active zone gets its lumens, every other
# light is set to 0 lm. No visibility toggling at all.
#
# >>> ONE-TIME MANUAL STEP <<<
#   Before running, UNHIDE all 13 light meshes in KeyShot (Linear Light 1-3,
#   Element 1-8, Conference 1-2). A hidden emissive mesh emits nothing, so they
#   must be visible for power control to work. Do this once; leave them on.
#
# SCENE FACTS (probed 2026-07-05):
#   zone "linears" -> meshes Linear Light 1..3, material "Office Light"
#                     (Area Light shader; params: color RGB, power float lumens)
#   zone "ceiling" -> meshes Element 1..8, Conference 1..2, material
#                     "Ceiling Spotlight" (Spotlight shader; same param names)
#   No colour-temperature param -> CCT is set as RGB.
#   Env: lux.getActiveEnvironment().setBrightness(v).  Exposure: saved 1 EV.
#   Base pass: HDRI on, all lights 0 lm.  Light pass: env ~0, one zone lit.
# ============================================================================

import lux
import os
import datetime

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
SUBMIT        = False
CAMERA_NAME   = "hero"

RENDERS_BASE  = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders"
ROUND_LABEL   = "2026-07-05_production-v1"
OUTPUT_DIR    = os.path.join(
    RENDERS_BASE,
    ROUND_LABEL or datetime.datetime.now().strftime("%Y-%m-%d_%H%M_lighting-test"))

RES_W         = 2560
RES_H         = 1600
SAMPLES       = 256          # doubled from 128 for production quality
# PNG, not EXR: KeyShot refuses to denoise a layered EXR ("Denoising will not
# apply to the individual render layers"). PNG denoises cleanly and is what the
# browser compositor uses directly. Tone mapping (1 EV, WB 0) is already dialed.
FORMAT_EXR    = False

BLACKOUT_ENV_FOR_LIGHT_PASSES = True
ENV_BLACK_BRIGHTNESS = 0.0001

# Zone -> material derived at runtime from the first member mesh.
ZONE_PROBE_MESH = {"linears": "Linear Light 1", "ceiling": "Element 1"}

KELVIN_RGB = {
    2400: (1.00, 0.56, 0.25),
    2700: (1.00, 0.64, 0.33),
    3000: (1.00, 0.70, 0.42),
    6500: (1.00, 0.99, 0.97),
}

# PRODUCTION pass set for the compositor. Locked recipe:
#   warm   = (1.00, 0.72, 0.45)   cool = c3 (0.42, 0.70, 1.00)
#   violet = (0.42, 0.20, 1.00)   (ceiling RGB accent, stylized)
# One pass per controllable state; base = ambient. Compositor crossfades
# warm<->cool per zone and blends the violet accent.
TEST_MATRIX = [
    {"zone": "linears", "tag": "warm",   "rgb": (1.00, 0.72, 0.45), "lumens": 20000},
    {"zone": "linears", "tag": "cool",   "rgb": (0.42, 0.70, 1.00), "lumens": 20000},
    {"zone": "ceiling", "tag": "warm",   "rgb": (1.00, 0.72, 0.45), "lumens": 5000},
    {"zone": "ceiling", "tag": "cool",   "rgb": (0.42, 0.70, 1.00), "lumens": 5000},
    {"zone": "ceiling", "tag": "violet", "rgb": (0.42, 0.20, 1.00), "lumens": 5000},
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
    if _tree is None: _tree = lux.getSceneTree()
    return _tree

def find(name):
    r = tree().find(name)
    if isinstance(r, (list, tuple)):
        return r[0] if r else None
    return r

def safe_param(node, name):
    try: return node.getParameter(name)
    except Exception: return None

# --- material lookups --------------------------------------------------------
_MATS = {}
def zone_material(zk):
    if zk not in _MATS:
        node = find(ZONE_PROBE_MESH[zk])
        _MATS[zk] = node.getMaterial() if node else None
    return _MATS[zk]

def power_nodes(mat):
    """All shader nodes in a material that carry a numeric 'power' param
    (Area Light or Spotlight emitter nodes)."""
    g = lux.getMaterialGraph(mat)
    out = []
    for sn in g.getNodes():
        p = safe_param(sn, "power")
        if p is None: continue
        try:
            if isinstance(p.getValue(), (int, float)):
                out.append(sn)
        except Exception:
            pass
    return out

def set_material(mat, lumens, color=None):
    """Set power (lumens) on every emitter node of the material, and colour if
    given. Setting all emitter nodes covers whichever sub-material renders."""
    for sn in power_nodes(mat):
        p = safe_param(sn, "power")
        if p: p.setValue(float(lumens))
        if color is not None:
            c = safe_param(sn, "color")
            if c: c.setValue(tuple(color))

def snapshot_material(mat):
    snap = []
    for sn in power_nodes(mat):
        p = safe_param(sn, "power"); c = safe_param(sn, "color")
        snap.append((sn.getID(),
                     p.getValue() if p else None,
                     c.getValue() if c else None))
    return (mat, snap)

def restore_material(snap):
    mat, nodes = snap
    g = lux.getMaterialGraph(mat)
    byid = {sn.getID(): sn for sn in g.getNodes()}
    for nid, power, color in nodes:
        sn = byid.get(nid)
        if not sn: continue
        if power is not None:
            p = safe_param(sn, "power")
            if p: p.setValue(power)
        if color is not None:
            c = safe_param(sn, "color")
            if c: c.setValue(color)

# --- environment -------------------------------------------------------------
def get_env():
    try: return lux.getActiveEnvironment()
    except Exception as e: log("  getActiveEnvironment failed: " + str(e)); return None

def set_env_brightness(v):
    env = get_env()
    if env:
        try: env.setBrightness(v)
        except Exception as e: log("  setBrightness failed: " + str(e))

# --- render ------------------------------------------------------------------
def render_options():
    opts = lux.getRenderOptions()
    # NOTE: DENOISE must be turned OFF in the Image tab. KS2026 scripted renders
    # cannot denoise ("Denoising will not apply to the individual render layers")
    # and will hard-error if it's on. We render clean-ish at 256 samples and
    # denoise the PNGs in post instead. Alpha also not output (additive/screen
    # compositing works on a black background without it).
    for setter, arg in [("setMaxSamplesRendering", SAMPLES),
                        ("setAddToQueue", True),
                        ("setOutputRenderLayers", False)]:
        fn = getattr(opts, setter, None)
        if fn:
            try: fn(arg)
            except Exception as e: log("  {0} failed: {1}".format(setter, e))
    return opts

def submit_pass(path):
    lux.setCamera(CAMERA_NAME)
    opts = render_options()   # setAddToQueue -> saves frozen scene copy now
    fmt = lux.RENDER_OUTPUT_EXR if FORMAT_EXR else lux.RENDER_OUTPUT_PNG
    lux.renderImage(path, width=RES_W, height=RES_H, opts=opts, format=fmt)
    log("  queued -> " + path)

# ============================================================================
# PHASES
# ============================================================================
def inspect():
    log("========= INSPECTION (no rendering) =========")
    log("Cameras: " + str(lux.getCameras()))
    env = get_env()
    if env: log("Env: {0} brightness={1}".format(env.getName(), env.getBrightness()))
    for zk in ZONE_PROBE_MESH:
        mat = zone_material(zk)
        nodes = power_nodes(mat) if mat else []
        log("zone '{0}': material={1!r}  emitter nodes:".format(zk, mat))
        for sn in nodes:
            log("   id={0} power={1} color={2}".format(
                sn.getID(),
                safe_param(sn,"power").getValue(),
                safe_param(sn,"color").getValue() if safe_param(sn,"color") else None))
    log("REMINDER: unhide all 13 light meshes once before SUBMIT=True.")
    log("=============================================")

def run_matrix():
    ensure_output_dir()
    zones = list(ZONE_PROBE_MESH.keys())
    snaps = {zk: snapshot_material(zone_material(zk)) for zk in zones}
    env0 = get_env().getBrightness() if get_env() else 1.0
    try:
        # BASE: all lights 0, HDRI on
        log("Base pass (all lights 0 lm, HDRI ambient):")
        for zk in zones: set_material(zone_material(zk), 0)
        set_env_brightness(env0)
        submit_pass(os.path.join(OUTPUT_DIR, "base_off." + ext()))

        # LIGHT PASSES: env blacked out; one zone lit, others 0
        if BLACKOUT_ENV_FOR_LIGHT_PASSES:
            set_env_brightness(ENV_BLACK_BRIGHTNESS)

        ok = fail = 0
        for spec in TEST_MATRIX:
            tag = "{0}_{1}".format(spec["zone"], spec["tag"])
            log("Pass: " + tag)
            try:
                color = spec["rgb"] if "rgb" in spec else KELVIN_RGB[spec["kelvin"]]
                for zk in zones:
                    if zk == spec["zone"]:
                        set_material(zone_material(zk), spec["lumens"], color)
                    else:
                        set_material(zone_material(zk), 0)
                log("  {0}: colour={1} power={2}lm".format(
                    zone_material(spec["zone"]),
                    tuple(round(c,3) for c in color), spec["lumens"]))
                submit_pass(os.path.join(OUTPUT_DIR, "light_{0}.{1}".format(tag, ext())))
                ok += 1
            except Exception as e:
                fail += 1; log("  PASS FAILED: " + str(e))
        log("==== queued {0} passes, {1} failed ====".format(ok, fail))
        log("Processing queue -> rendering locally on GPU (race-free)...")
        lux.processQueue()
        log("processQueue() returned.")
    finally:
        set_env_brightness(env0)
        for zk in zones: restore_material(snaps[zk])
        log("Scene state restored (env brightness, light power+colour).")

def main():
    log("KeyShot lighting test (power-only) - SUBMIT={0}, format={1}".format(SUBMIT, ext()))
    if SUBMIT: run_matrix()
    else:      inspect()

main()
