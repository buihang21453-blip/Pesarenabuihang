(function () {
  'use strict';
  var shell = document.getElementById('roomLiveShell');
  var panel = document.getElementById('roomV2AssetTester');
  if (!shell || !panel) return;

  var storageKey = 'pesArenaRoomUiAssetTest.v129';
  var defaultCenter = shell.style.getPropertyValue('--room-v2-center-bg') || '';

  function setActive(selector, value) {
    panel.querySelectorAll(selector).forEach(function (button) {
      button.classList.toggle('is-active', button.dataset.centerSrc === value);
    });
  }

  function apply(state, persist) {
    if (state.centerSrc) {
      shell.style.setProperty('--room-v2-center-bg', 'url("' + state.centerSrc + '")');
      setActive('[data-center-src]', state.centerSrc);
    }
    if (persist) {
      try { localStorage.setItem(storageKey, JSON.stringify(state)); } catch (e) {}
    }
  }

  panel.querySelectorAll('[data-center-src]').forEach(function (button) {
    button.addEventListener('click', function () {
      var current = readState();
      current.centerSrc = button.dataset.centerSrc;
      apply(current, true);
    });
  });
  function readState() {
    try { return JSON.parse(localStorage.getItem(storageKey) || '{}') || {}; }
    catch (e) { return {}; }
  }

  var reset = panel.querySelector('[data-room-ui-reset]');
  if (reset) reset.addEventListener('click', function () {
    try { localStorage.removeItem(storageKey); } catch (e) {}
    shell.style.setProperty('--room-v2-center-bg', defaultCenter);
    panel.querySelectorAll('.is-active').forEach(function (el) { el.classList.remove('is-active'); });
  });

  apply(readState(), false);
})();
