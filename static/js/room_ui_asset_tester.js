(function () {
  'use strict';
  var shell = document.getElementById('roomLiveShell');
  var panel = document.getElementById('roomV2AssetTester');
  if (!shell || !panel) return;

  var roomStorageKey = 'pesArenaRoomUiAssetTest.v132';
  var projectLogoStorageKey = 'pesArenaProjectLogoTest.v132';
  var defaultCenter = shell.style.getPropertyValue('--room-v2-center-bg') || '';
  var projectLogo = document.querySelector('.sidebar-brand-logo');
  var defaultProjectLogo = projectLogo ? projectLogo.getAttribute('src') : '';

  function setActive(selector, dataKey, value) {
    panel.querySelectorAll(selector).forEach(function (button) {
      button.classList.toggle('is-active', button.dataset[dataKey] === value);
    });
  }

  function readJson(key) {
    try { return JSON.parse(localStorage.getItem(key) || '{}') || {}; }
    catch (e) { return {}; }
  }

  function applyRoom(state, persist) {
    if (state.centerSrc) {
      shell.style.setProperty('--room-v2-center-bg', 'url("' + state.centerSrc + '")');
      setActive('[data-center-src]', 'centerSrc', state.centerSrc);
    }
    if (persist) {
      try { localStorage.setItem(roomStorageKey, JSON.stringify(state)); } catch (e) {}
    }
  }

  function applyProjectLogo(src, persist) {
    if (!src || !projectLogo) return;
    projectLogo.setAttribute('src', src);
    setActive('[data-project-logo-src]', 'projectLogoSrc', src);
    if (persist) {
      try { localStorage.setItem(projectLogoStorageKey, src); } catch (e) {}
    }
  }

  panel.querySelectorAll('[data-center-src]').forEach(function (button) {
    button.addEventListener('click', function () {
      var current = readJson(roomStorageKey);
      current.centerSrc = button.dataset.centerSrc;
      applyRoom(current, true);
    });
  });

  panel.querySelectorAll('[data-project-logo-src]').forEach(function (button) {
    button.addEventListener('click', function () {
      applyProjectLogo(button.dataset.projectLogoSrc, true);
    });
  });

  var reset = panel.querySelector('[data-room-ui-reset]');
  if (reset) reset.addEventListener('click', function () {
    try {
      localStorage.removeItem(roomStorageKey);
      localStorage.removeItem(projectLogoStorageKey);
    } catch (e) {}
    shell.style.setProperty('--room-v2-center-bg', defaultCenter);
    if (projectLogo && defaultProjectLogo) projectLogo.setAttribute('src', defaultProjectLogo);
    panel.querySelectorAll('.is-active').forEach(function (el) { el.classList.remove('is-active'); });
  });

  applyRoom(readJson(roomStorageKey), false);
  try {
    var savedProjectLogo = localStorage.getItem(projectLogoStorageKey) || '';
    if (savedProjectLogo) applyProjectLogo(savedProjectLogo, false);
  } catch (e) {}
})();
