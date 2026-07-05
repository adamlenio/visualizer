// GET /api/network?networkId=...&sessionId=...
// Server-side proxy that returns network info, units, and scenes in one call.
//
// The API key stays server-side for these REST calls; only the sessionId is
// held by the browser after auth.

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.CASAMBI_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'Server missing CASAMBI_API_KEY' });
  }

  const { networkId, sessionId } = req.query;
  if (!networkId || !sessionId) {
    return res.status(400).json({ error: 'networkId and sessionId query params required' });
  }

  const headers = {
    'Content-Type': 'application/json',
    'X-Casambi-Key': apiKey,
    'X-Casambi-Session': String(sessionId),
  };

  const base = `https://door.casambi.com/v1/networks/${encodeURIComponent(String(networkId))}`;

  async function fetchJSON(url) {
    const r = await fetch(url, { headers });
    const text = await r.text();
    let json = null;
    try { json = JSON.parse(text); } catch { /* ignore */ }
    return { ok: r.ok, status: r.status, json, text };
  }

  try {
    const [info, units, scenes, state] = await Promise.all([
      fetchJSON(base),
      fetchJSON(`${base}/units`),
      fetchJSON(`${base}/scenes`),
      fetchJSON(`${base}/state`),
    ]);

    // If any of the calls failed with 401/403, surface auth error clearly.
    const authFail = [info, units, scenes, state].find(
      (r) => r.status === 401 || r.status === 403
    );
    if (authFail) {
      return res.status(401).json({
        error: 'Casambi session unauthorized',
        detail: authFail.json || authFail.text,
      });
    }

    return res.status(200).json({
      info: info.json,
      units: units.json,
      scenes: scenes.json,
      state: state.json,
      errors: {
        info: info.ok ? null : { status: info.status, body: info.json || info.text },
        units: units.ok ? null : { status: units.status, body: units.json || units.text },
        scenes: scenes.ok ? null : { status: scenes.status, body: scenes.json || scenes.text },
        state: state.ok ? null : { status: state.status, body: state.json || state.text },
      },
    });
  } catch (err) {
    return res.status(500).json({ error: 'Fetch failed', detail: String(err) });
  }
}
