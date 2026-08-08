(function () {
  'use strict';

  function config() {
    return window.PES_PRESENCE_CONFIG || {};
  }

  function postHeartbeat() {
    const cfg = config();
    if (!cfg.heartbeatUrl) return Promise.resolve();
    const task = function () {
      return fetch(cfg.heartbeatUrl, {
        method: 'POST',
        credentials: 'same-origin',
        cache: 'no-store'
      }).catch(function () {});
    };
    return window.PESNet && typeof window.PESNet.singleFlight === 'function'
      ? window.PESNet.singleFlight('api:heartbeat', task)
      : task();
  }

  function start() {
    const cfg = config();
    if (!cfg.enabled || !window.PESNet || typeof window.PESNet.createPoller !== 'function') return;

    window.PESPresence = window.PESPresence || {};
    if (window.PESPresence.started) return;
    window.PESPresence.started = true;
    window.PESPresence.postHeartbeat = postHeartbeat;

    window.PESPresence.poller = window.PESNet.createPoller({
      key: 'heartbeat',
      task: postHeartbeat,
      visibleInterval: Number(cfg.visibleInterval || 30000),
      hiddenInterval: Number(cfg.hiddenInterval || 60000),
      runWhenHidden: true,
      immediate: true,
      jitter: Number(cfg.jitter || 3000)
    });

    let lastResumeAt = 0;
    function heartbeatOnResume() {
      const now = Date.now();
      if (now - lastResumeAt < 5000) return;
      lastResumeAt = now;
      postHeartbeat();
    }

    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) heartbeatOnResume();
    });
    window.addEventListener('focus', heartbeatOnResume);
  }

  window.PESPresence = window.PESPresence || {};
  window.PESPresence.postHeartbeat = postHeartbeat;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, {once: true});
  } else {
    start();
  }
})();
