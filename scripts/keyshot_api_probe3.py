# -*- coding: utf-8 -*-
# ============================================================================
# KeyShot 2026 (15.1) API PROBE 3 - scene save + render queue / network
# Goal: find how to FREEZE each pass into its own file and submit to the farm,
# so per-pass state (colour/power/visibility) is captured correctly.
# No rendering. Paste the WHOLE output back to Claude.
# ============================================================================
import lux

def log(m): print("[probe3] " + str(m))
def filt(names, keys):
    return sorted([n for n in names if any(k.lower() in n.lower() for k in keys)])

ln = dir(lux)
log("save/export : " + str(filt(ln, ["save", "export", "package", "bip", "write", "backup"])))
log("queue/net   : " + str(filt(ln, ["queue", "network", "submit", "job", "config", "frame", "batch"])))
log("scene io    : " + str(filt(ln, ["open", "load", "import", "newscene", "file"])))

# help() for the most promising candidates
for name in ["savePackage", "saveFile", "saveScene", "save",
             "processQueue", "renderConfiguration", "renderFrames",
             "addToRenderQueue", "renderImage"]:
    fn = getattr(lux, name, None)
    if fn:
        log("================ help(lux.%s) ================" % name)
        try: help(fn)
        except Exception as e: log("help failed: " + str(e))
    else:
        log("lux.%s : NOT PRESENT" % name)

# RenderOptions queue-related setters
log("================ RenderOptions queue/network setters ================")
opts = lux.getRenderOptions()
log("opts queue/net methods: " + str(filt(dir(opts), ["queue", "network", "add", "send", "output", "name"])))
for m in ["setAddToQueue", "setSendToNetwork"]:
    fn = getattr(opts, m, None)
    if fn:
        log("---- help(RenderOptions.%s) ----" % m)
        try: help(fn)
        except Exception as e: log("help failed: " + str(e))
log("================ END PROBE 3 ================")
