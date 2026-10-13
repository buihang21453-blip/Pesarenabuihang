(function () {
  "use strict";
  const cfg = window.PES_REALTIME_CONFIG || {};
  let client = null, userChannel = null, presenceChannel = null;
  let connected = false;
  const roomChannels = new Map();

  function dispatch(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail: detail || {} }));
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
        dispatch("pes:realtime-user-event", { event: message.event, payload: message.payload || {} });
      }).subscribe(function (status) {
        connected = status === "SUBSCRIBED" || connected;
        if (["CHANNEL_ERROR", "TIMED_OUT", "CLOSED"].includes(status)) connected = false;
        dispatch("pes:realtime-status", { connected: connected, status: status });
      });
    }
    // Presence is connection-level and intentionally carries no profile/game data.
    if (cfg.presenceKey) {
      presenceChannel = client.channel("pes-online-presence", {
        config: { presence: { key: cfg.presenceKey } }
      });
      presenceChannel.subscribe(function (status) {
        if (status === "SUBSCRIBED") {
          presenceChannel.track({ online_at: new Date().toISOString() });
          // Reconnect is a good moment to refresh the DB fallback timestamp once.
          fetch("/heartbeat", { method: "POST", credentials: "same-origin", cache: "no-store" }).catch(function () {});
        }
      });
    }
  }
  function subscribeRoom(topic, handler) {
    if (!client || !topic || roomChannels.has(topic)) return roomChannels.get(topic) || null;
    const channel = client.channel(topic, { config: { broadcast: { self: false } } });
    channel.on("broadcast", { event: "*" }, function (message) {
      if (typeof handler === "function") handler(message.event, message.payload || {});
      dispatch("pes:realtime-room-event", { topic: topic, event: message.event, payload: message.payload || {} });
    }).subscribe();
    roomChannels.set(topic, channel);
    return channel;
  }
  function unsubscribeRoom(topic) {
    const ch = roomChannels.get(topic);
    if (client && ch) client.removeChannel(ch);
    roomChannels.delete(topic);
  }
  window.PESRealtime = {
    init: init,
    isConnected: function () { return !!connected; },
    subscribeRoom: subscribeRoom,
    unsubscribeRoom: unsubscribeRoom
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
