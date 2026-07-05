// casambi-client.js
// Browser-side Casambi Cloud API client.
//
// Flow:
//   1. login()            → POST /api/session, get { networkId, sessionId, wsKey }
//   2. loadNetwork()      → GET  /api/network, get units + scenes + state
//   3. connectWebSocket() → wss://door.casambi.com/v1/bridge/, open wire
//   4. sendControl/scene  → outgoing controlUnit / controlScene frames
//   5. events             → 'ready', 'status', 'unitChanged', 'error'
//
// This client is intentionally standalone (no framework, no build step).

(function (global) {
  'use strict';

  const WS_URL = 'wss://door.casambi.com/v1/bridge/';
  const REST_SESSION = '/api/session';
  const REST_NETWORK = '/api/network';

  function uuid() {
    // RFC4122-ish; good enough for a wire ref
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  class CasambiClient {
    constructor(opts) {
      opts = opts || {};
      this.wireId = opts.wireId || 1;
      this.reconnectMs = opts.reconnectMs || 3000;
      this.autoReconnect = opts.autoReconnect !== false;

      this.session = null; // { networkId, sessionId, wsKey, name }
      this.network = null; // { info, units, scenes, state }
      this.ws = null;
      this.wsReady = false;
      this.status = 'disconnected'; // disconnected | connecting | connected | error

      this._listeners = {};
      this._reconnectTimer = null;
      this._closing = false;
    }

    on(event, fn) {
      (this._listeners[event] = this._listeners[event] || []).push(fn);
      return this;
    }

    _emit(event, payload) {
      (this._listeners[event] || []).forEach(function (fn) {
        try { fn(payload); } catch (e) { console.error('[casambi] listener error', e); }
      });
    }

    _setStatus(s, detail) {
      this.status = s;
      this._emit('status', { status: s, detail: detail || null });
    }

    async login() {
      this._setStatus('connecting', 'auth');
      const resp = await fetch(REST_SESSION, { method: 'POST' });
      const data = await resp.json();
      if (!resp.ok) {
        this._setStatus('error', data);
        throw new Error('login failed: ' + JSON.stringify(data));
      }
      this.session = data;
      return data;
    }

    async loadNetwork() {
      if (!this.session) throw new Error('login() first');
      const q = new URLSearchParams({
        networkId: this.session.networkId,
        sessionId: this.session.sessionId,
      });
      const resp = await fetch(REST_NETWORK + '?' + q.toString());
      const data = await resp.json();
      if (!resp.ok) {
        this._setStatus('error', data);
        throw new Error('loadNetwork failed: ' + JSON.stringify(data));
      }
      this.network = data;
      return data;
    }

    connectWebSocket() {
      if (!this.session) throw new Error('login() first');
      if (this.ws) { try { this.ws.close(); } catch (e) {} }

      this._setStatus('connecting', 'ws');
      // Casambi expects the API key as WebSocket subprotocol.
      const ws = new WebSocket(WS_URL, this.session.wsKey);
      this.ws = ws;
      this.wsReady = false;

      const self = this;
      ws.onopen = function () {
        const openMsg = {
          method: 'open',
          id: parseInt(self.session.networkId, 10),
          session: self.session.sessionId,
          ref: uuid(),
          wire: self.wireId,
          type: 1, // FRONTEND client
        };
        ws.send(JSON.stringify(openMsg));
      };

      ws.onmessage = function (evt) {
        let msg = null;
        try { msg = JSON.parse(evt.data); } catch (e) { return; }
        self._handleMessage(msg);
      };

      ws.onerror = function (err) {
        console.error('[casambi] ws error', err);
        self._emit('error', { source: 'ws', err: String(err) });
        self._setStatus('error', 'ws error');
      };

      ws.onclose = function () {
        self.wsReady = false;
        self._setStatus('disconnected', 'ws closed');
        if (self.autoReconnect && !self._closing) {
          clearTimeout(self._reconnectTimer);
          self._reconnectTimer = setTimeout(function () {
            self.connectWebSocket();
          }, self.reconnectMs);
        }
      };
    }

    _handleMessage(msg) {
      // Wire open ack
      if (msg.wireStatus === 'openWireSucceed') {
        this.wsReady = true;
        this._setStatus('connected', 'wire open');
        this._emit('ready', msg);
        return;
      }
      // Failure codes documented by Casambi
      const failCodes = [
        'keyAuthenticateFailed',
        'keyAuthorizeFailed',
        'invalidSession',
        'invalidValueType',
        'invalidData',
      ];
      if (msg.wireStatus && failCodes.indexOf(msg.wireStatus) >= 0) {
        this._setStatus('error', msg.wireStatus);
        this._emit('error', { source: 'wire', code: msg.wireStatus, msg: msg });
        return;
      }
      if (msg.method === 'peerChanged') {
        // Peer joined/left. If online true after open, treat as ready.
        if (!this.wsReady && msg.online === true) {
          this.wsReady = true;
          this._setStatus('connected', 'peer online');
          this._emit('ready', msg);
        }
        this._emit('peerChanged', msg);
        return;
      }
      if (msg.method === 'unitChanged') {
        this._emit('unitChanged', msg);
        return;
      }
      if (msg.method === 'networkUpdated') {
        this._emit('networkUpdated', msg);
        return;
      }
      this._emit('message', msg);
    }

    _send(obj) {
      if (!this.ws || this.ws.readyState !== 1) {
        console.warn('[casambi] ws not open, dropped', obj);
        return false;
      }
      this.ws.send(JSON.stringify(obj));
      return true;
    }

    // ─── Control API ──────────────────────────────────────────────

    // Set a unit's dimmer (0..1)
    setUnitDimmer(unitId, value) {
      return this._send({
        wire: this.wireId,
        method: 'controlUnit',
        id: parseInt(unitId, 10),
        targetControls: { Dimmer: { value: clamp01(value) } },
      });
    }

    // Set colour temperature in Kelvin
    setUnitCCT(unitId, kelvin) {
      return this._send({
        wire: this.wireId,
        method: 'controlUnit',
        id: parseInt(unitId, 10),
        targetControls: {
          ColorTemperature: { value: Math.round(kelvin) },
          Colorsource: { source: 'TW' },
        },
      });
    }

    // Set RGB colour (0..255)
    setUnitRGB(unitId, r, g, b) {
      return this._send({
        wire: this.wireId,
        method: 'controlUnit',
        id: parseInt(unitId, 10),
        targetControls: {
          RGB: { rgb: 'rgb(' + r + ', ' + g + ', ' + b + ')' },
          Colorsource: { source: 'RGB' },
        },
      });
    }

    // Set arbitrary targetControls dictionary
    setUnitControls(unitId, targetControls) {
      return this._send({
        wire: this.wireId,
        method: 'controlUnit',
        id: parseInt(unitId, 10),
        targetControls: targetControls,
      });
    }

    controlScene(sceneId, level) {
      return this._send({
        wire: this.wireId,
        method: 'controlScene',
        id: parseInt(sceneId, 10),
        level: level, // 0 = off, 1 = on
      });
    }

    close() {
      this._closing = true;
      clearTimeout(this._reconnectTimer);
      if (this.ws) {
        try {
          this._send({ method: 'close', wire: this.wireId });
          this.ws.close();
        } catch (e) {}
      }
    }
  }

  function clamp01(v) {
    v = +v;
    if (!isFinite(v)) return 0;
    if (v < 0) return 0;
    if (v > 1) return 1;
    return v;
  }

  global.CasambiClient = CasambiClient;
})(window);
