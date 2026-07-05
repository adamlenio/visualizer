#!/usr/bin/env node
// Standalone auth test — verifies the network-session flow end-to-end.
//
//   export CASAMBI_API_KEY='...'
//   export CASAMBI_EMAIL='admin@cbridge.local'
//   export CASAMBI_PASSWORD='...'
//   node scripts/test-auth.mjs
//
// Optionally set STEP=session|units|scenes|state|ws to run only that step.

const step = process.env.STEP || 'all';
const key = process.env.CASAMBI_API_KEY;
const email = process.env.CASAMBI_EMAIL;
const password = process.env.CASAMBI_PASSWORD;

if (!key || !email || !password) {
  console.error('Missing env: CASAMBI_API_KEY / CASAMBI_EMAIL / CASAMBI_PASSWORD');
  process.exit(2);
}

async function post(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'X-Casambi-Key': key, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  let json = null; try { json = JSON.parse(text); } catch {}
  return { status: r.status, json, text };
}

async function get(url, sessionId) {
  const r = await fetch(url, {
    headers: {
      'X-Casambi-Key': key,
      'X-Casambi-Session': sessionId,
      'Content-Type': 'application/json',
    },
  });
  const text = await r.text();
  let json = null; try { json = JSON.parse(text); } catch {}
  return { status: r.status, json, text };
}

(async () => {
  console.log('=== 1. POST /v1/networks/session/ ===');
  const s = await post('https://door.casambi.com/v1/networks/session/', { email, password });
  console.log('  status:', s.status);
  if (s.status !== 200) {
    console.log('  body:', s.text.slice(0, 500));
    process.exit(1);
  }
  const netId = Object.keys(s.json)[0];
  const sess = s.json[netId].sessionId;
  const name = s.json[netId].name;
  console.log('  networkId:', netId, '  name:', name, '  sessionId:', sess.slice(0, 12) + '…');

  if (step !== 'all' && step !== 'session') return;

  console.log('\n=== 2. GET /v1/networks/{id} ===');
  const info = await get('https://door.casambi.com/v1/networks/' + netId, sess);
  console.log('  status:', info.status);
  if (info.json) console.log('  keys:', Object.keys(info.json));

  console.log('\n=== 3. GET /v1/networks/{id}/units ===');
  const units = await get('https://door.casambi.com/v1/networks/' + netId + '/units', sess);
  console.log('  status:', units.status);
  if (units.json) {
    const list = Array.isArray(units.json) ? units.json : Object.values(units.json);
    console.log('  unit count:', list.length);
    list.slice(0, 8).forEach(u => console.log('    -', u.id, u.name, '  fixture', u.fixtureId));
  }

  console.log('\n=== 4. GET /v1/networks/{id}/scenes ===');
  const scenes = await get('https://door.casambi.com/v1/networks/' + netId + '/scenes', sess);
  console.log('  status:', scenes.status);
  if (scenes.json) {
    const list = Array.isArray(scenes.json) ? scenes.json : Object.values(scenes.json);
    console.log('  scene count:', list.length);
    list.slice(0, 8).forEach(sc => console.log('    -', sc.id, sc.name));
  }

  console.log('\n=== 5. GET /v1/networks/{id}/state ===');
  const state = await get('https://door.casambi.com/v1/networks/' + netId + '/state', sess);
  console.log('  status:', state.status);
  if (state.json) console.log('  keys:', Object.keys(state.json).slice(0, 20));

  if (step !== 'all' && step !== 'ws') return;

  console.log('\n=== 6. WebSocket open ===');
  let WebSocket;
  try {
    WebSocket = (await import('ws')).default;
  } catch {
    console.log('  npm i ws  (skipping ws test — module not installed)');
    return;
  }
  const ws = new WebSocket('wss://door.casambi.com/v1/bridge/', key);
  await new Promise((resolve) => {
    let done = false;
    const timeout = setTimeout(() => { if (!done) { done = true; ws.close(); console.log('  timeout'); resolve(); } }, 10000);
    ws.on('open', () => {
      const openMsg = {
        method: 'open', id: parseInt(netId, 10), session: sess,
        ref: 'test-' + Date.now(), wire: 1, type: 1,
      };
      ws.send(JSON.stringify(openMsg));
    });
    ws.on('message', (data) => {
      console.log('  RX:', data.toString().slice(0, 400));
      if (!done) { done = true; clearTimeout(timeout); setTimeout(() => { ws.close(); resolve(); }, 500); }
    });
    ws.on('error', (e) => { console.log('  WS ERR', e.message); if (!done) { done = true; clearTimeout(timeout); resolve(); } });
  });
})().catch(e => { console.error('FATAL', e); process.exit(1); });
