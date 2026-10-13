(function () {
  "use strict";
  const cfg = window.PES_REALTIME_CONFIG || {};
  let client = null, userChannel = null, presenceChannel = null, globalChannel = null;
  let connected = false, everConnected = false, lastHeartbeatAt = 0;
  const roomChannels = new Map();
  const tournamentChannels = new Map();
  const USER_EVENTS = new Set(["INVITE_CHANGED", "MATCH_FOUND", "ROOM_ASSIGNED"]);
  const ROOM_EVENTS = new Set(["CHAT_CHANGED", "PLAYER_READY", "ROOM_CHANGED"]);
  const GLOBAL_EVENTS = new Set(["GLOBAL_CHAT_CHANGED"]);
  const TOURNAMENT_EVENTS = new Set(["TOURNAMENT_CHANGED", "HOST_READY_CHANGED"]);

  function dispatch(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail: detail || {} }));
  }
  function setMainStatus(status) {
    const wasConnected = connected;
    connected = status === "SUBSCRIBED";
    if (connected) {
      const recovered = everConnected && !wasConnected;
      everConnected = true;
      dispatch("pes:realtime-status", { connected: true, status: status, recovered: recovered });
      if (recovered) dispatch("pes:realtime-resync", { reason: "reconnected" });
    } else {
      dispatch("pes:realtime-status", { connected: false, status: status });
    }
  }
  function heartbeatAfterReconnect() {
    const now = Date.now();
    if (now - lastHeartbeatAt < 300000) return;
    lastHeartbeatAt = now;
    fetch("/heartbeat", { method: "POST", credentials: "same-origin", cache: "no-store" }).catch(function () {});
  }
  function init() {
    if (!cfg.enabled || !cfg.url || !cfg.key || !window.supabase || !window.supabase.createClient) {
      dispatch("pes:realtime-status", { connected: false, reason: "unavailable" });
      return;
    }
    client = window.supabase.createClient(cfg.url, cfg.key, {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
      realtime: { params: { eventsPerSecond: 10 } }
    });
    if (cfg.userTopic) {
      userChannel = client.channel(cfg.userTopic, { config: { broadcast: { self: false } } });
      userChannel.on("broadcast", { event: "*" }, function (message) {
        const eventName = String(message && message.event || "");
        if (!USER_EVENTS.has(eventName)) return; // unknown/forged signals never affect UI
        dispatch("pes:realtime-user-event", { event: eventName, payload: { changed: true } });
      }).subscribe(setMainStatus);
    }
    if (cfg.globalTopic) {
      globalChannel = client.channel(cfg.globalTopic, { config: { broadcast: { self: false } } });
      globalChannel.on("broadcast", { event: "*" }, function (message) {
        const eventName = String(message && message.event || "");
        if (!GLOBAL_EVENTS.has(eventName)) return;
        dispatch("pes:realtime-global-event", { event: eventName, payload: { changed: true } });
      }).subscribe(function () {});
    }
    if (cfg.presenceKey) {
      presenceChannel = client.channel("pes-online-presence", {
        config: { presence: { key: cfg.presenceKey } }
      });
      presenceChannel.subscribe(function (status) {
        if (status === "SUBSCRIBED") {
          presenceChannel.track({ online_at: new Date().toISOString() });
          heartbeatAfterReconnect();
        }
      });
    }
    window.addEventListener("online", function () {
      // Supabase reconnects automatically. Resync immediately so missed events cannot leave stale UI.
      dispatch("pes:realtime-resync", { reason: "browser-online" });
    });
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) dispatch("pes:realtime-resync", { reason: "tab-visible" });
    });
  }
  function subscribeRoom(topic, handler) {
    if (!client || !topic) return null;
    if (roomChannels.has(topic)) return roomChannels.get(topic).channel;
    const entry = { channel: null, connected: false, everConnected: false };
    const channel = client.channel(topic, { config: { broadcast: { self: false } } });
    entry.channel = channel;
    channel.on("broadcast", { event: "*" }, function (message) {
      const eventName = String(message && message.event || "");
      if (!ROOM_EVENTS.has(eventName)) return;
      if (typeof handler === "function") handler(eventName, { changed: true });
      dispatch("pes:realtime-room-event", { topic: topic, event: eventName, payload: { changed: true } });
    }).subscribe(function (status) {
      const wasConnected = entry.connected;
      entry.connected = status === "SUBSCRIBED";
      const recovered = entry.connected && entry.everConnected && !wasConnected;
      if (entry.connected) entry.everConnected = true;
      dispatch("pes:realtime-room-status", { topic: topic, connected: entry.connected, status: status, recovered: recovered });
      if (recovered) {
        if (typeof handler === "function") handler("__RESYNC__", { changed: true });
        dispatch("pes:realtime-resync", { reason: "room-reconnected", topic: topic });
      }
    });
    roomChannels.set(topic, entry);
    return channel;
  }
  function subscribeTournament(topic, handler) {
    if (!client || !topic) return null;
    if (tournamentChannels.has(topic)) return tournamentChannels.get(topic).channel;
    const entry = { channel: null, connected: false };
    const channel = client.channel(topic, { config: { broadcast: { self: false } } });
    entry.channel = channel;
    channel.on("broadcast", { event: "*" }, function (message) {
      const eventName = String(message && message.event || "");
      if (!TOURNAMENT_EVENTS.has(eventName)) return;
      if (typeof handler === "function") handler(eventName, { changed: true });
      dispatch("pes:realtime-tournament-event", { topic: topic, event: eventName, payload: { changed: true } });
    }).subscribe(function (status) { entry.connected = status === "SUBSCRIBED"; });
    tournamentChannels.set(topic, entry);
    return channel;
  }
  function unsubscribeRoom(topic) {
    const entry = roomChannels.get(topic);
    if (client && entry && entry.channel) client.removeChannel(entry.channel);
    roomChannels.delete(topic);
  }
  window.PESRealtime = {
    init: init,
    isConnected: function () { return !!connected; },
    isRoomConnected: function (topic) { const e = roomChannels.get(topic); return !!(e && e.connected); },
    subscribeRoom: subscribeRoom,
    unsubscribeRoom: unsubscribeRoom,
    subscribeTournament: subscribeTournament
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
