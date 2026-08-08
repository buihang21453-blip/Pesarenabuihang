(function PESBlackBoxBootstrap(){
  'use strict';
  const cfg = window.PES_BLACKBOX_CONFIG || {};
  if (!cfg.enabled || !cfg.ingestUrl || window.__PES_BLACKBOX_STARTED__) return;
  window.__PES_BLACKBOX_STARTED__ = true;

  const sidKey = 'pes_blackbox_session_id';
  let sessionId = sessionStorage.getItem(sidKey);
  if (!sessionId) {
    sessionId = 'bb-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2,10);
    try { sessionStorage.setItem(sidKey, sessionId); } catch (_) {}
  }
  const buffer = [];
  const maxBuffer = Number(cfg.maxBuffer || 200);
  const batchSize = Number(cfg.batchSize || 20);
  const flushMs = Number(cfg.flushMs || 10000);
  const slowApiMs = Number(cfg.slowApiMs || 2500);
  let flushing = false;

  const redact = (value) => {
    if (value == null) return value;
    if (typeof value === 'string') return value.slice(0, 1200);
    if (Array.isArray(value)) return value.slice(0, 30).map(redact);
    if (typeof value === 'object') {
      const out = {};
      Object.keys(value).slice(0, 50).forEach((key) => {
        out[key] = /password|secret|token|authorization|cookie|session|parsec/i.test(key) ? '[redacted]' : redact(value[key]);
      });
      return out;
    }
    return value;
  };

  function push(type, data, level){
    try {
      buffer.push({ type, level: level || 'INFO', ts: new Date().toISOString(), ...redact(data || {}) });
      while (buffer.length > maxBuffer) buffer.shift();
      if (buffer.length >= batchSize) flush(false);
    } catch (_) {}
  }

  function payload(events){
    return JSON.stringify({
      session_id: sessionId,
      page: location.pathname + location.search,
      client: {
        browser: navigator.userAgent.slice(0, 500),
        viewport: { width: innerWidth, height: innerHeight },
        online: navigator.onLine,
        visibility: document.visibilityState,
        app_version: cfg.appVersion || null
      },
      events
    });
  }

  function flush(useBeacon){
    if (flushing || !buffer.length) return Promise.resolve();
    const events = buffer.splice(0, Math.min(buffer.length, 80));
    const body = payload(events);
    if (useBeacon && navigator.sendBeacon) {
      try {
        if (navigator.sendBeacon(cfg.ingestUrl, new Blob([body], {type:'application/json'}))) return Promise.resolve();
      } catch (_) {}
    }
    flushing = true;
    return fetch(cfg.ingestUrl, {
      method:'POST', credentials:'same-origin', keepalive:true,
      headers:{'Content-Type':'application/json'}, body
    }).catch(function(){
      // Fail-open and keep only a bounded retry slice.
      Array.prototype.unshift.apply(buffer, events.slice(-20));
      while (buffer.length > maxBuffer) buffer.shift();
    }).finally(function(){ flushing = false; });
  }

  window.PESBlackBox = {
    capture: push,
    flush: function(){ return flush(false); },
    getSessionId: function(){ return sessionId; },
    getRecentEvents: function(){ return buffer.slice(-100); },
    getDiagnostics: function(){
      return {
        enabled: true,
        bufferLength: buffer.length,
        maxBuffer: maxBuffer,
        batchSize: batchSize,
        flushMs: flushMs,
        slowApiMs: slowApiMs,
        networkWrapped: !!cfg.captureNetwork,
        clicksCaptured: !!cfg.captureClicks
      };
    },
    microBenchmark: function(iterations){
      const n = Math.max(100, Math.min(Number(iterations || 5000), 20000));
      const sample = {type:'benchmark', message:'blackbox micro benchmark', payload:{a:1,b:'x',token:'secret'}};
      const t0 = performance.now();
      for (let i=0; i<n; i++) {
        redact(sample);
      }
      const elapsed = performance.now() - t0;
      return {iterations:n, totalMs:Number(elapsed.toFixed(3)), perOperationMs:Number((elapsed/n).toFixed(6))};
    }
  };

  window.addEventListener('error', function(e){
    push('js_error', {message:e.message, source:e.filename, line:e.lineno, column:e.colno}, 'ERROR');
  }, true);
  window.addEventListener('unhandledrejection', function(e){
    let msg = '';
    try { msg = e.reason && (e.reason.stack || e.reason.message || String(e.reason)); } catch (_) {}
    push('unhandled_rejection', {message:msg}, 'ERROR');
  });

  if (cfg.captureClicks) {
    document.addEventListener('click', function(e){
      const el = e.target && e.target.closest ? e.target.closest('button,a,[role="button"],input[type="submit"]') : null;
      if (!el) return;
      push('ui_click', {
        tag: el.tagName,
        id: el.id || null,
        name: el.getAttribute('name') || null,
        action: el.getAttribute('data-action') || null,
        text: (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0,120)
      });
    }, true);
  }

  if (cfg.captureNetwork && window.fetch) {
    const originalFetch = window.fetch.bind(window);
    window.fetch = function(input, init){
      const method = String((init && init.method) || 'GET').toUpperCase();
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      if (url.indexOf('/api/blackbox/') !== -1) return originalFetch(input, init);
      const started = performance.now();
      return originalFetch(input, init).then(function(res){
        const ms = Math.round(performance.now() - started);
        if (!res.ok || ms >= slowApiMs) push(ms >= slowApiMs ? 'api_slow' : 'api_error', {method,url:url.slice(0,500),status:res.status,duration_ms:ms}, !res.ok ? 'ERROR':'WARNING');
        return res;
      }).catch(function(err){
        push('api_error', {method,url:url.slice(0,500),duration_ms:Math.round(performance.now()-started),message:String(err && err.message || err)}, 'ERROR');
        throw err;
      });
    };
  }

  push('page_view', {title:document.title, referrer:document.referrer.slice(0,500)});
  window.addEventListener('online', function(){ push('network_online'); });
  window.addEventListener('offline', function(){ push('network_offline', {}, 'WARNING'); });
  document.addEventListener('visibilitychange', function(){ push('visibility_change', {state:document.visibilityState}); });
  window.addEventListener('pagehide', function(){ push('page_hide'); flush(true); });
  setInterval(function(){ if (!document.hidden) flush(false); }, flushMs);
})();
