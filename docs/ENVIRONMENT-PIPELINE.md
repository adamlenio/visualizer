# Environment Pipeline — from 3D model to live Visualizer page

How we take each of the 8 remaining environments (Hospitality, Retail, Art & Culture,
Education, Worship, Healthcare, Residential, Outdoor) from nothing to a live page like
office.html. Based on the proven Office pipeline (July 2026 sprint).

## Division of labor

| Step | Who | Tool |
|---|---|---|
| 0. Lighting design brief | Claude | Web research (designinglighting.com refs) |
| 1. Source & buy 3D model | Claude shortlists, Adam buys | Marketplaces |
| 2. Source fixture models | Claude shortlists, Adam downloads | BIMobject / mfr sites |
| 3. Import model into KeyShot | Adam (GUI) | KeyShot 2026 |
| 4. Scene inspection | Claude writes script, Adam runs | lux scripting console |
| 5. KeyShot material assignment | Claude writes script, Adam runs + approves look | lux |
| 6. Emissive/luminaire setup | Claude writes script, Adam runs | lux |
| 7. Render pass submission | Claude writes script, Adam runs | lux → farm (unlimited) |
| 8. EXR → JPEG compositing/export | Claude | sandbox Python |
| 9. Web page build | Claude | clone office.html |
| 10. QA + deploy | Both | vercel |

Steps 4–7 use the write→run→paste-output loop we used for the Office. Alternative:
Adam can enable Computer Use in Cowork and Claude drives KeyShot directly (imports,
material assignment, test renders) — worth trying on environment #1 to see if it's faster.

## Step 0 — Lighting design brief (per environment)

Before buying anything, Claude produces a 1-page brief per vertical using reference
photography (designinglighting.com and similar):

- **Light layers**: ambient / task / accent / decorative — what a lighting designer
  would spec for this space type
- **Fixture schedule**: types (downlight, linear, track, pendant, wall grazer,
  candle-effect...), rough counts, zoning → these become the web app's Groups
- **Color story**: CCT range, where RGBW color makes a compelling demo
  (e.g. Worship: grazing stone + stained-glass accent; Retail: display pop)
- **Camera views**: hero + 2–3 alternates (View 1/2/3 slots in the UI)

## Step 1 — Environment model criteria

- FBX or OBJ included (KeyShot cannot import .max)
- Textures included, UV-mapped, real-world scale
- **Modeled light fixtures are a big plus** — believable source geometry sells the
  render. Their materials get replaced with our Area Light setup, so the *baked
  lighting* doesn't matter; the *fixture geometry* does.
- Missing/wrong fixtures are fine — we add our own (Step 2)
- Poly count is a non-issue for stills (Office proved 5M+ OK)

Current shortlist: `environment-model-shortlist.md` (session outputs, July 8) —
church $69, mall $34.50, school library $10, etc.

## Step 2 — Fixture models (the "lighting designer" layer)

To make spaces read as professionally designed, add real fixture geometry:

- **BIMobject.com** — free manufacturer-accurate models (filter Revit/SketchUp/OBJ)
- **Manufacturer sites** — many Casambi-ecosystem brands publish 3D/BIM files;
  using real Casambi-ready fixtures is also a marketing story ("that's an actual
  fixture you can buy")
- **Marketplaces** — generic pendants/tracks/downlights, $2–15 each

Naming convention (critical — scripts and web IDs derive from it):
mesh/group names `<zone>_<n>` e.g. `pendant_1`, `track_3`, `graze_2`.
One emissive material per zone (like Office's "Office Light" / "Ceiling Spotlight").

## Steps 3–6 — KeyShot scene build

1. Adam imports FBX (GUI), saves .bip into the project
2. Claude's **inspection script** dumps scene tree + materials → paste output back
3. Claude's **material script** assigns KeyShot-native materials by mapping imported
   material names (wood, stone, fabric, glass, metal...) → Adam runs, test-renders,
   gives look feedback, iterate
4. Claude's **luminaire script** builds Area Light emissives per zone:
   - Area Light shader: `color` (RGB), `power` (lumens), `lumen`=1 — no CCT param,
     set CCT as RGB via KELVIN_RGB table (already calibrated in keyshot_lighting_run.py)
   - Fixture housings get self-glow material so fixtures read as "on" in passes

## Step 7 — Render passes (the proven recipe)

Non-negotiables learned on the Office:

- Exposure locked in Image Style (1 EV) — identical tone mapping across ALL passes
- `lux.setCamera(name)` before EVERY render (camera drift bug)
- Base pass: HDRI at original brightness, all luminaires off
- Light passes: env brightness 0.0001 (blackout), ONE luminaire on per pass
- Per luminaire: R, G, B, W passes (W = calibrated white, not RGB-mixed)
- EXR + alpha, farm submit via `opts.setSendToNetwork(True)`
- Farm is unlimited — render generous test matrices, don't ration
- Output naming: `light_<id>_<C>.exr` → matches web layer convention directly

Pass count per environment ≈ 1 + 4×(luminaire count). Office = 53. Keep individually
controllable luminaires ≤ ~15 per environment; decorative multiples can share a zone
pass (one layer controlled as a group) to cap layer count and decoded-image RAM.

## Step 8 — Post (Claude, sandbox)

EXR → JPEG q60 at 2560px (`assets/<env>_full/`) + 1280px (`assets/<env>_1280/`)
srcset pair. Consistency check: histogram-compare passes, verify black floor on
blackout passes, confirm additive stack ≈ all-on reference render.

## Step 9 — Web build (Claude)

Clone office.html → `<env>.html`:
- `LUMS` / `GROUPS` arrays from the fixture schedule (Step 0 brief)
- Asset paths, cache-bust version, env name/branding
- Homepage card: Coming soon → ● Live
- Same perf rules: screen-blend layers, display:none when off, reduced-motion guard

## Step 10 — QA + deploy

- All layers load (onerror check), mobile 1280 srcset verified
- Decoded-RAM budget check on phone-class device
- Lighthouse pass, then vercel deploy

## Recommended order

1. **Education** ($10 school library) — cheapest full-pipeline shakedown
2. **Worship** — highest visual drama (volume, stained glass, grazing) = best demo
3. **Retail** — strong commercial story for Casambi reps
4. Hospitality → Art & Culture → Healthcare → Residential → Outdoor
   (Outdoor last: different lighting physics — facades, pole/landscape fixtures,
   night-base instead of daylight slider)
