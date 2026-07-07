# Casambi Visualizer — Technical Onboarding

**For:** Eric Lenio · **From:** Adam (AD&M) · **Repo:** `adamlenio/visualizer` · **Live:** https://visualizer-lenio1.vercel.app

## What it is

A browser-based, **photorealistic lighting visualizer**. You control a rendered room with a UI that mirrors the Casambi mobile app, and the room updates in real time — dim/color/CCT per luminaire, per group, and per scene. The visualization is **image compositing of pre-rendered light passes**, not a 3D engine, so it runs anywhere with zero GPU cost on the client. Today one environment is live (an Office); the model is many verticals (Office, Hospitality, Retail, Art & Culture, Education, Worship, Healthcare, Residential, Outdoor), plus interactive training and rep lead-gen.

## Repo layout

```
public/
  index.html          # marketing homepage (AD&M-branded) -> links into the demo
  office.html         # THE app: split-screen room + Casambi-style phone UI (self-contained HTML/CSS/JS)
  casambi-client.js   # Casambi Cloud API client (REST + WebSocket) — scaffolded, not yet live
  assets/office_full2/ # 53 optimized render passes (2560px JPEG q60) the compositor stacks
api/
  session.js          # Vercel serverless: POST /api/session  -> door.casambi.com auth (keeps API key server-side)
  network.js          # Vercel serverless: GET  /api/network  -> units/scenes/state
scripts/              # KeyShot lux render pipeline (Python) + API probes
vercel.json           # cleanUrls, no-store on /api, no-cache on html
renders/              # raw KeyShot output (gitignored — large)
```

Deploy: GitHub `master` → Vercel (project `visualizer`). Production is promoted manually today; setting Production Branch → `master` makes pushes auto-deploy.

## 1) Render pipeline (KeyShot 2026 → per-luminaire RGBW passes)

Each of the 13 fixtures is rendered **in isolation, four times** — Red, Green, Blue, and a clean **White** primary — on a black environment, plus one ambient `base` pass. So 13×4 + 1 = **53 passes** at 2560×1600, 768 samples, via `scripts/keyshot_rgb_render.py` on a KeyShot Network render farm.

Hard-won KeyShot 2026 lux-API facts (documented in-code, worth knowing before you touch it):
- **Isolation is by material-swap, not visibility.** `SceneNode.hide()` is a one-way toggle that can't reliably reveal a mesh; material *duplication* via `setMaterial(link=False)` silently no-ops. What works: swap every *other* fixture's mesh to a non-emitting material for each pass, leaving only the target lit.
- **Scripted renders can't denoise** (KeyShot errors). We render at high samples and **denoise in post** (OpenCV NLM) during the asset-optimization step.
- **Farm submission is async and races** on rapid multi-pass batches — must insert a delay (~4s) between `setSendToNetwork` submits, or use the local queue.
- CCT: the mesh-light shader has **no Kelvin param**; color is RGB, so CCT is expressed as RGB.

Post-process: `renders/ → public/assets/office_full2/` = downscale/denoise → JPEG q60. (Larger pixels + heavier compression beat smaller + light compression at equal size.)

## 2) The compositor (public/office.html)

All client-side, no framework. The room is a stack of `<img>` layers with `mix-blend-mode: screen` over a `base` image; **per-layer opacity is the only thing that changes at runtime**, so realtime control is just cheap opacity writes (GPU-composited). Off layers get `display:none` after fade to keep the compositor light.

Per-luminaire state: `{ on, level, mode:'white'|'color', rgb, sat, cct }`. Compositing math per fixture (L = on·level):
- **White mode:** `W = L`, with a small R/B tint from `cct`. The dedicated W pass gives a *clean* neutral white (RGB-mixed white had a cast on this room).
- **Color mode:** `W = L·(1−sat)`, `R/G/B = L·hue·sat`. So the color-wheel **center = true white** (blends the W layer), edge = saturated hue — which makes White↔Color switching seamless.
- Groups (Master / Linear / Downlights / Conference) just fan a change out to member IDs; group tile = representative of members.
- A **Daylight** slider dims the ambient `base` (CSS brightness) so color reads dramatically at "dusk" and neutrally at "day."

UI mirrors the real app: Luminaires / Gallery / Scenes / Settings tabs, tap-to-select, control sheet with an HSV color wheel + brightness + warm↔cool + power. Plus a guided **Learn** tour and a **Talk to a Rep** CTA.

## 3) Casambi Cloud API scaffold (where it's NOT done yet)

`casambi-client.js` + the two serverless functions implement the documented flow: `login()` → `/api/session` (server-side key) → `loadNetwork()` → `/api/network` → `connectWebSocket()` → `wss://door.casambi.com/v1/bridge/`, with outgoing `controlUnit`/`controlScene` frames and incoming `unitChanged` folded back into UI state. **It is written but unproven** — it needs a real Casambi network to authenticate against, and one open credential question (the local bridge login `admin@cbridge.local` vs. the cloud account the REST session endpoint expects).

## Where your expertise plugs in (the interesting problems)

1. **Multi-user / virtual networks — the big architectural unknown.** For a *public* site, many visitors each need their own independent room state, with no shared-network collisions. This is a multi-tenant session-isolation problem. Options: (a) a real Casambi "virtual" (hardware-less) network per session if the API supports it — TBD with Casambi's US technical lead; (b) our own per-session simulation of the app's behavior (groups/scenes/schedules/color) with the real API used only where it helps. Your multi-tenant SaaS background is the best fit on the team for owning this.
2. **Persistence & accounts** — save/share a configured scene, resumable sessions, per-visitor state. None of this exists yet.
3. **Lead-gen → document generation (LincDoc fit).** Turn a saved scene into an auto-generated **lighting spec / proposal / Casambi tender-text PDF** routed to a rep — converting the demo into a lead-to-quote engine. This is squarely LincDoc territory.
4. **Training certification** — the guided tour is meant to carry Casambi "Level 1" training; completion → issued certificate (again, LincDoc).

## Run it locally

Static site — open `public/office.html` in a browser (it loads `assets/office_full2/` relatively). For the serverless API + WebSocket, run `vercel dev` at repo root (see `README.md`), with `CASAMBI_API_KEY` / `CASAMBI_EMAIL` / `CASAMBI_PASSWORD` env vars.

## Status & near-term backlog

Live and deployed. Fast-follows: advanced guided-tour overlays (spotlight rings + interaction-gated steps) for Level-1 training; multi-angle Gallery views (new KeyShot cameras → per-view RGBW sets); in-app group/scene building; smoother manual→scene crossfade; and resolving the Casambi virtual-network/multi-user question.
