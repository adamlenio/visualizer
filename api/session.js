// POST /api/session
// Creates a Casambi network session using server-side credentials.
// Returns { networkId, sessionId, wsKey } to the browser.
//
// Environment variables required (set in Vercel dashboard):
//   CASAMBI_API_KEY   – developer API key from Casambi
//   CASAMBI_EMAIL     – network name (email format), e.g. admin@cbridge.local
//   CASAMBI_PASSWORD  – network password
//
// The wsKey field is the Casambi API key. The browser needs it to open the
// WebSocket (Casambi passes the key as a WebSocket subprotocol). This is
// consistent with how the official Casambi web dashboards work. Treat the
// key as a client-visible secret and rotate it in the developer portal if
// exposure is a concern.

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.CASAMBI_API_KEY;
  const email = process.env.CASAMBI_EMAIL;
  const password = process.env.CASAMBI_PASSWORD;

  if (!apiKey || !email || !password) {
    return res.status(500).json({
      error: 'Server missing Casambi credentials',
      missing: {
        CASAMBI_API_KEY: !apiKey,
        CASAMBI_EMAIL: !email,
        CASAMBI_PASSWORD: !password,
      },
    });
  }

  try {
    const resp = await fetch('https://door.casambi.com/v1/networks/session/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Casambi-Key': apiKey,
      },
      body: JSON.stringify({ email, password }),
    });

    const bodyText = await resp.text();
    let data;
    try {
      data = JSON.parse(bodyText);
    } catch {
      return res.status(502).json({
        error: 'Non-JSON response from Casambi',
        status: resp.status,
        body: bodyText.slice(0, 500),
      });
    }

    if (!resp.ok) {
      return res.status(resp.status).json({
        error: 'Casambi network session failed',
        status: resp.status,
        detail: data,
      });
    }

    // Response shape: { "<networkId>": { sessionId, name, ... }, ... }
    const networkIds = Object.keys(data);
    if (networkIds.length === 0) {
      return res.status(502).json({ error: 'No networks in session response' });
    }

    const networkId = networkIds[0];
    const sessionId = data[networkId].sessionId;
    const name = data[networkId].name || '';

    return res.status(200).json({
      networkId,
      sessionId,
      name,
      wsKey: apiKey,
      networks: data,
    });
  } catch (err) {
    return res.status(500).json({ error: 'Fetch failed', detail: String(err) });
  }
}
