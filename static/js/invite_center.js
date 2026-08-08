(function () {
  'use strict';

  const state = {
    lastInviteId: null,
    countdownTimer: null,
    requestPromise: null,
    lastPollAt: 0
  };

  function cfg() { return window.PES_INVITE_CONFIG || {}; }
  function esc(value) {
    if (typeof window.escapeHtml === 'function') return window.escapeHtml(String(value == null ? '' : value));
    const div = document.createElement('div');
    div.innerText = String(value == null ? '' : value);
    return div.innerHTML;
  }
  function avatar(invite) {
    if (typeof window.renderAvatarHtml === 'function') {
      return window.renderAvatarHtml(
        invite.from_avatar_url,
        invite.from_name,
        'lg',
        invite.from_achievement,
        invite.from_avatar_frame && invite.from_avatar_frame.image_url
      );
    }
    return `<span class="player-avatar player-avatar-fallback">${esc((invite.from_name || '?').charAt(0))}</span>`;
  }

  function hidePopup() {
    const backdrop = document.getElementById('inviteModalBackdrop');
    if (backdrop) backdrop.style.display = 'none';
    if (state.countdownTimer) clearInterval(state.countdownTimer);
    state.countdownTimer = null;
    state.lastInviteId = null;
  }

  function renderInvitePopup(invite) {
    const backdrop = document.getElementById('inviteModalBackdrop');
    const content = document.getElementById('inviteModalContent');
    if (!backdrop || !content || !invite) return;

    state.lastInviteId = invite.id;
    content.innerHTML = `
      <div class="invite-modal-player">
        <div class="invite-modal-person">
          ${avatar(invite)}
          <p><strong>${esc(invite.from_name)}</strong> đang mời bạn thi đấu.</p>
        </div>
        <p class="small">Rank: ${esc(invite.from_rank)} • Điểm: ${esc(invite.from_points)} • Tier: ${esc(invite.tier)}</p>
        <p class="small">Lời mời hết hạn sau <strong id="inviteCountdown">${esc(invite.expires_in_seconds || 0)}</strong> giây.</p>
      </div>
      <div class="invite-modal-actions">
        <form method="post" action="${esc(invite.accept_url)}">
          <button class="btn invite-action-btn is-accept" name="action" value="accept" type="submit">Chấp nhận</button>
        </form>
        <form method="post" action="${esc(invite.reject_url)}">
          <button class="btn invite-action-btn is-reject" name="action" value="reject" type="submit">Từ chối</button>
        </form>
      </div>`;

    backdrop.style.display = 'flex';
    if (state.countdownTimer) clearInterval(state.countdownTimer);
    let seconds = Number(invite.expires_in_seconds || 0);
    state.countdownTimer = window.setInterval(function () {
      seconds = Math.max(0, seconds - 1);
      const node = document.getElementById('inviteCountdown');
      if (node) node.textContent = String(seconds);
      if (seconds <= 0) hidePopup();
    }, 1000);
  }

  function checkPendingInvites() {
    const url = cfg().pendingUrl;
    state.lastPollAt = Date.now();
    if (!url) return Promise.resolve();

    const task = function () {
      return fetch(url, {method: 'GET', credentials: 'same-origin', cache: 'no-store'})
        .then(function (res) {
          if (res.status === 204) return {invites: []};
          if (!res.ok) throw new Error('invite_poll_http_' + res.status);
          return res.json();
        })
        .then(function (data) {
          if (!data.invites || data.invites.length === 0) {
            hidePopup();
            return;
          }
          const invite = data.invites[0];
          if (invite.id !== state.lastInviteId) renderInvitePopup(invite);
        })
        .catch(function () {});
    };

    if (window.PESNet && typeof window.PESNet.singleFlight === 'function') {
      return window.PESNet.singleFlight('api:pending-invites', task);
    }
    if (state.requestPromise) return state.requestPromise;
    state.requestPromise = Promise.resolve().then(task).finally(function () { state.requestPromise = null; });
    return state.requestPromise;
  }

  window.PESInviteCenter = {
    checkPendingInvites: checkPendingInvites,
    renderInvitePopup: renderInvitePopup,
    hidePopup: hidePopup,
    getLastPollAt: function () { return state.lastPollAt; }
  };
  // Compatibility for existing event-driven hooks in base.html.
  window.checkPendingInvites = checkPendingInvites;
})();
