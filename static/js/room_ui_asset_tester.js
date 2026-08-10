(function () {
  'use strict';
  var shell = document.getElementById('roomLiveShell');
  var panel = document.getElementById('roomV2AssetTester');
  var brand = document.getElementById('roomV2BrandImage');
  if (!shell || !panel || !brand) return;

  var storageKey = 'pesArenaRoomUiAssetTest.v129';
  var defaultCenter = shell.style.getPropertyValue('--room-v2-center-bg') || '';
  var defaultBrand = brand.getAttribute('data-default-src') || brand.src;

  function setActive(selector, value) {
    panel.querySelectorAll(selector).forEach(function (button) {
      var key = selector.indexOf('center') >= 0 ? 'centerSrc' : 'brandSrc';
      button.classList.toggle('is-active', button.dataset[key] === value);
    });
  }

  function apply(state, persist) {
    if (state.centerSrc) {
      shell.style.setProperty('--room-v2-center-bg', 'url("' + state.centerSrc + '")');
      setActive('[data-center-src]', state.centerSrc);
    }
    if (state.brandSrc) {
      brand.src = state.brandSrc;
      setActive('[data-brand-src]', state.brandSrc);
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
  panel.querySelectorAll('[data-brand-src]').forEach(function (button) {
    button.addEventListener('click', function () {
      var current = readState();
      current.brandSrc = button.dataset.brandSrc;
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
    brand.src = defaultBrand;
    panel.querySelectorAll('.is-active').forEach(function (el) { el.classList.remove('is-active'); });
  });

  apply(readState(), false);
})();
