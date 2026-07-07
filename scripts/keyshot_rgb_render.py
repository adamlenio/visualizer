# -*- coding: utf-8 -*-
# ============================================================================
# Casambi Visualizer - PER-LUMINAIRE RGB RENDER  (material-swap isolation)
# KeyShot 2026. Renders each of the 13 fixtures individually in R/G/B primaries
# so the compositor can drive ANY colour per luminaire (and groups = sums).
#
# ISOLATION METHOD (no material duplication needed - it doesn't work in KS2026):
#   For each pass, every OTHER fixture's mesh is swapped to a dark, non-emitting
#   material; only the target fixture keeps its light material. Setting that
#   light material's colour/power therefore affects only the target. Meshes are
#   swapped with setMaterial(link=True) (proven to work); the scene is restored
#   at the end.
#
# FARM: setSendToNetwork + SUBMIT_DELAY between jobs (proven reliable).
# PREREQ for a CLEAN re-render: Denoise ON in the Image tab AND 'render all layers'
#   OFF. Denoise conflicts with render-layers output (that was the old error); with
#   layers off, native KeyShot denoise runs and is far cleaner than post-NLM.
#   Samples can drop (~384-512) since denoise cleans residual noise -> faster too.
#
# MODE:
#   "test" -> 3 quick passes (linear_1 R, element_5 G, base) to VERIFY isolation
#             and colour before the big run. Low res/samples.
#   "full" -> all 40 passes at production res/samples.
# ============================================================================
import lux, os, time

MODE         = "full"        # "test" then "full"
CAMERA_NAME  = "hero"
BASE_DIR     = "/Users/adamleniopro/Claude/Projects/Casambi Visualizer Cowork/renders"
SUBMIT_DELAY = 4.0           # seconds between farm submits
ENV_BLACK    = 0.0001
NON_EMIT     = "Modern Office - Black Plastic"   # existing non-light material
ZONE_MAT     = {"lin": "Office Light", "cei": "Ceiling Spotlight"}
ZONE_POWER   = {"lin": 15000.0, "cei": 6000.0}
PRIMARIES    = [("R", (1.0, 0.0, 0.0)), ("G", (0.0, 1.0, 0.0)), ("B", (0.0, 0.0, 1.0)),
                ("W", (1.0, 1.0, 1.0))]   # W = clean neutral white primary (RGBW)

# fixture -> (mesh name, zone, friendly id)
LUMINAIRES = [
    ("Linear Light 1", "lin", "linear_1"),
    ("Linear Light 2", "lin", "linear_2"),
    ("Linear Light 3", "lin", "linear_3"),
    ("Element 1", "cei", "element_1"), ("Element 2", "cei", "element_2"),
    ("Element 3", "cei", "element_3"), ("Element 4", "cei", "element_4"),
    ("Element 5", "cei", "element_5"), ("Element 6", "cei", "element_6"),
    ("Element 7", "cei", "element_7"), ("Element 8", "cei", "element_8"),
    ("Conference 1", "cei", "conference_1"), ("Conference 2", "cei", "conference_2"),
]

if MODE == "test":
    OUT = os.path.join(BASE_DIR, "2026-07-05_rgb-test")
    RES_W, RES_H, SAMPLES = 1280, 800, 48
else:
    OUT = os.path.join(BASE_DIR, "2026-07-05_rgbw-final")
    RES_W, RES_H, SAMPLES = 2560, 1600, 768   # overnight high-sample RGBW run

def log(m): print("[rgb] " + str(m))
tree = lux.getSceneTree()
def find(n):
    r = tree.find(n)
    return (r[0] if r else None) if isinstance(r,(list,tuple)) else r
def safe_param(node,nm):
    try: return node.getParameter(nm)
    except Exception: return None

def set_material(mat, lumens, color=None):
    g = lux.getMaterialGraph(mat)
    for sn in g.getNodes():
        p = safe_param(sn,"power")
        if p is None: continue
        try:
            if not isinstance(p.getValue(),(int,float)): continue
        except Exception: continue
        p.setValue(float(lumens))
        if color is not None:
            c = safe_param(sn,"color")
            if c: c.setValue(tuple(color))

def isolate(active_mesh, active_zone):
    """Only active_mesh keeps its light material; all others go dark."""
    for mesh, zone, fid in LUMINAIRES:
        n = find(mesh)
        if n is None: continue
        if mesh == active_mesh:
            n.setMaterial(ZONE_MAT[zone], link=True)
        else:
            n.setMaterial(NON_EMIT, link=True)

def env(v):
    try: lux.getActiveEnvironment().setBrightness(v)
    except Exception as e: log("env err: "+str(e))

def submit(path):
    lux.setCamera(CAMERA_NAME)
    opts = lux.getRenderOptions()
    try: opts.setMaxSamplesRendering(SAMPLES)
    except Exception: pass
    try: opts.setOutputRenderLayers(False)   # keep layers off so native denoise runs
    except Exception: pass
    opts.setSendToNetwork(True)
    lux.renderImage(path, width=RES_W, height=RES_H, opts=opts, format=lux.RENDER_OUTPUT_PNG)
    log("  submitted -> " + os.path.basename(path))

def restore():
    """Put every fixture back on its zone light material at 0 lm; env on."""
    for mesh, zone, fid in LUMINAIRES:
        n = find(mesh)
        if n: n.setMaterial(ZONE_MAT[zone], link=True)
    for z in ZONE_MAT.values():
        set_material(z, 0)
    env(1.0)
    log("Scene restored (fixtures back on light materials, 0 lm, env on).")

# --- pass list ---------------------------------------------------------------
def all_passes():
    passes = []
    for mesh, zone, fid in LUMINAIRES:
        for pname, rgb in PRIMARIES:
            passes.append((mesh, zone, fid, pname, rgb))
    return passes

def test_passes():
    return [("Linear Light 1","lin","linear_1","R",(1.0,0.0,0.0)),
            ("Element 5","cei","element_5","G",(0.0,1.0,0.0))]

# --- run ---------------------------------------------------------------------
def main():
    if not os.path.isdir(OUT): os.makedirs(OUT)
    log("MODE=%s  out=%s  %dx%d s=%d" % (MODE, OUT, RES_W, RES_H, SAMPLES))
    passes = test_passes() if MODE == "test" else all_passes()
    try:
        # BASE: normal room, all fixtures on light mats at 0 lm, env on
        restore()
        submit(os.path.join(OUT, "base." + "png"))
        time.sleep(SUBMIT_DELAY)

        # PRIMARY passes: env black, isolate one fixture, set its colour+power
        env(ENV_BLACK)
        for i,(mesh, zone, fid, pname, rgb) in enumerate(passes):
            isolate(mesh, zone)
            set_material(ZONE_MAT[zone], ZONE_POWER[zone], rgb)
            submit(os.path.join(OUT, "light_%s_%s.png" % (fid, pname)))
            if i < len(passes)-1:
                time.sleep(SUBMIT_DELAY)
        log("==== submitted %d passes + base to farm ====" % len(passes))
    finally:
        restore()

main()
