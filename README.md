# Casambi Visualizer

Browser-based interactive lighting visualization platform, integrating with the
Casambi Cloud API for real-time device state and control.

## Architecture

```
Browser (index.html + casambi-client.js)
  │
  ├─ POST /api/session      →  door.casambi.com/v1/networks/session/
  ├─ GET  /api/network      →  door.casambi.com/v1/networks/{id}(/units|/scenes|/state)
  └─ wss://door.casambi.com/v1/bridge/   (direct, api key as WS subprotocol)
```

- REST auth and topology fetches go through Vercel serverless functions so the
  API key stays server-side.
- The WebSocket is opened directly from the browser using the API key as the
  WebSocket subprotocol (this is how Casambi expects browser clients to
  connect). The key is returned from `/api/session` as `wsKey` after
  successful auth.

## Deploy to Vercel

1. Push this repo to GitHub (`git push origin main`).
2. Visit https://vercel.com/new and import the repo.
3. Framework preset: **Other** (no framework detected — that's correct).
4. Root directory: repo root. Build command: leave blank. Output directory:
   `public` (Vercel auto-detects this from the folder layout).
5. Under **Environment Variables**, add these three encrypted variables and
   apply them to Production, Preview, and Development:

   | Name                | Value                                    |
   |---------------------|------------------------------------------|
   | `CASAMBI_API_KEY`   | your developer API key from Casambi      |
   | `CASAMBI_EMAIL`     | network name (e.g. `admin@cbridge.local`)|
   | `CASAMBI_PASSWORD`  | network password                         |

6. Deploy. First deploy produces a `*.vercel.app` URL.

## Local development

```
npm install -g vercel
vercel link
vercel env pull   # pulls env vars into .env.local
vercel dev
```

Then open http://localhost:3000.

## Sanity-check the API before deploy

```
export CASAMBI_API_KEY='...'
export CASAMBI_EMAIL='admin@cbridge.local'
export CASAMBI_PASSWORD='...'
node scripts/test-auth.mjs
```

This exercises session → info → units → scenes → state → WebSocket in one go
and prints unit / scene lists.

## Files

```
api/
  session.js         – POST proxy for network-session auth
  network.js         – GET proxy for network info + units + scenes + state
public/
  index.html         – Casambi app UI + compositor + integration
  casambi-client.js  – Browser WebSocket + REST client
scripts/
  test-auth.mjs      – Standalone Node script for verifying API access
vercel.json          – Vercel routing/caching config
```

## Behaviour

On page load:

1. `bootstrap()` renders the compositor with the fallback ZONES/SCENES.
2. It calls `/api/session` → gets `networkId`, `sessionId`, `wsKey`.
3. It calls `/api/network` → gets units, scenes, state → merges them into
   `ZONES` and `SCENES` in place.
4. It opens the WebSocket with the API key as subprotocol, sends the `open`
   frame, and listens for `unitChanged`, `peerChanged`, `networkUpdated`.
5. Every UI control (dimmer slider, CCT slider, luminaire tap, scene tap,
   All-luminaires toggle) fires the local visual update AND a matching
   WebSocket control frame.

If any step from (2) onward fails, the visualization stays in demo mode using
the hardcoded ZONES/SCENES. A red or grey banner surfaces the connection
state. This preserves the pitch demo when the gateway is offline.

## Casambi API reference

- REST: `POST https://door.casambi.com/v1/networks/session/`
  Headers: `X-Casambi-Key`; Body: `{ email, password }`
  Returns: `{ "<networkId>": { sessionId, name, ... } }`
- REST: `GET https://door.casambi.com/v1/networks/{id}/units`
  Headers: `X-Casambi-Key`, `X-Casambi-Session`
- WebSocket: `wss://door.casambi.com/v1/bridge/`
  Subprotocol: `<api_key>`
  Open frame: `{ method:"open", id:networkId, session:sessionId, wire:1, type:1, ref:<uuid> }`
- Control frame: `{ wire, method:"controlUnit", id:unitId, targetControls:{Dimmer:{value:0..1}} }`
- Scene frame: `{ wire, method:"controlScene", id:sceneId, level:0|1 }`

## Security notes

- The API key is never checked into the repo. It is server-side only for REST
  and passed to the browser only after a successful `/api/session` call for
  WebSocket use.
- The network password is server-side only. It never reaches the browser.
- The session ID is short-lived (weeks/months per Casambi docs) and lives in
  memory in the client tab; it is not persisted.

## Next steps

- Replace demo SVG polygons in the visualization with the Photoshop-masked
  PNG layers per zone.
- Populate the `unitByZone` mapping to align real Casambi units with the
  rendered zone visuals.
- Add scene metadata (colour, icon) via a `data-scene.json` in `public/` so
  designers can theme the scene tiles.
