(() => {
  const root = document.querySelector('[data-room-ui-designer]');
  if (!root) return;
  const preview = root.querySelector('[data-room-ui-preview]');
  const previewViewport = root.querySelector('[data-room-ui-preview-viewport]');
  const previewShell = root.querySelector('[data-room-ui-preview-shell]');

  let fitFrame = 0;
  function fitWholePreview() {
    if (!preview || !previewViewport) return;
    cancelAnimationFrame(fitFrame);
    fitFrame = requestAnimationFrame(() => {
      preview.style.transform = 'none';
      preview.classList.remove('is-auto-fit');
      const naturalWidth = Math.max(preview.scrollWidth, 1180);
      const naturalHeight = Math.max(preview.scrollHeight, 1);
      const availableWidth = Math.max(previewViewport.clientWidth, 1);
      const viewportCap = window.innerWidth > 760
        ? Math.max(250, Math.min(window.innerHeight * 0.47, 500))
        : Math.max(220, Math.min(window.innerHeight * 0.5, 420));
      const scale = Math.min(1, availableWidth / naturalWidth, viewportCap / naturalHeight);
      preview.style.transform = `scale(${scale})`;
      previewViewport.style.height = `${Math.ceil(naturalHeight * scale)}px`;
      preview.classList.add('is-auto-fit');
      if (previewShell && window.innerWidth > 760) {
        const headH = previewShell.querySelector('.room-ui-preview-head')?.offsetHeight || 0;
        previewShell.style.maxHeight = `${Math.ceil(naturalHeight * scale + headH + 28)}px`;
      } else if (previewShell) {
        previewShell.style.maxHeight = '';
      }
    });
  }
  const inputs = [...root.querySelectorAll('[data-room-ui-input]')];
  const cssMap = {
    player_width:'--p-player', center_width:'--p-center', sidebar_width:'--p-side',
    main_height:'--p-height', main_gap:'--p-main-gap', mode_gap:'--p-mode-gap', header_height:'--p-header-h', share_button_width:'--p-share-w', share_button_height:'--p-share-h', share_button_font_size:'--p-share-font',
    player_panel_y:'--p-player-y', center_y:'--p-center-y', sidebar_y:'--p-side-y',
    brand_scale:'--p-brand-scale', brand_y:'--p-brand-y',
    avatar_scale:'--p-avatar-scale', avatar_y:'--p-avatar-y',
    player_name_scale:'--p-name-scale', player_name_y:'--p-name-y',
    club_logo_scale:'--p-club-scale', club_area_y:'--p-club-y',
    active_mode_logo_scale:'--p-active-scale', active_mode_logo_size:'--p-active-size', active_mode_logo_y:'--p-active-y',
    vs_scale:'--p-vs-scale', vs_y:'--p-vs-y',
    center_gap:'--p-center-gap', center_padding_y:'--p-center-pad-y',
    center_action_gap:'--p-action-gap', center_button_height:'--p-button-h', center_button_font_size:'--p-button-font', center_action_width:'--p-action-w',
    mode_logo_size:'--p-mode-size', mode_card_height:'--p-card-height', mode_cluster_height:'--p-mode-cluster-h', mode_status_width:'--p-status-width',
    rail_parsec_ratio:'--p-rail-parsec', rail_room_history_ratio:'--p-rail-history', rail_h2h_ratio:'--p-rail-h2h', rail_gap:'--p-rail-gap', right_rail_font_size:'--p-right-font',
    panel_opacity:'--p-opacity', header_opacity:'--p-header-opacity', host_panel_opacity:'--p-host-opacity', center_panel_opacity:'--p-center-opacity', opponent_panel_opacity:'--p-away-opacity', sidebar_panel_opacity:'--p-side-opacity', mode_card_opacity:'--p-mode-opacity', action_zone_opacity:'--p-action-opacity', background_opacity:'--p-bg-opacity', gold_glow:'--p-glow'
  };
  const pxUnits = new Set(['main_height','main_gap','mode_gap','header_height','share_button_width','share_button_height','share_button_font_size','player_panel_y','center_y','sidebar_y','brand_y','avatar_y','player_name_y','club_area_y','active_mode_logo_y','vs_y','center_gap','center_padding_y','center_action_gap','center_button_height','center_button_font_size','mode_logo_size','mode_card_height','mode_cluster_height','rail_gap','right_rail_font_size']);
  const frUnits = new Set(['player_width','center_width','sidebar_width','rail_parsec_ratio','rail_room_history_ratio','rail_h2h_ratio']);
  const percentUnits = new Set(['center_action_width','mode_status_width']);

  function apply(input) {
    const key = input.dataset.roomUiInput;
    const value = input.value;
    const output = root.querySelector(`[data-output-for="${key}"]`);
    if (output) output.value = value;
    if (!preview || !cssMap[key]) return;
    let suffix = pxUnits.has(key) ? 'px' : frUnits.has(key) ? 'fr' : percentUnits.has(key) ? '%' : '';
    preview.style.setProperty(cssMap[key], `${value}${suffix}`);
    fitWholePreview();
  }
  inputs.forEach(input => { apply(input); input.addEventListener('input', () => apply(input)); });

  root.querySelectorAll('[data-room-ui-tab]').forEach(button => button.addEventListener('click', () => {
    const key = button.dataset.roomUiTab;
    root.querySelectorAll('[data-room-ui-tab]').forEach(b => b.classList.toggle('active', b === button));
    root.querySelectorAll('[data-room-ui-panel]').forEach(panel => panel.classList.toggle('active', panel.dataset.roomUiPanel === key));
    fitWholePreview();
  }));

  const stateLabels = {waiting:'CHỜ ĐỐI THỦ',ready:'CHỜ SẴN SÀNG',playing:'ĐANG THI ĐẤU',confirm:'CHỜ XÁC NHẬN',confirmed:'ĐÃ XÁC NHẬN',rematch:'ĐÁ TIẾP'};
  root.querySelectorAll('[data-room-ui-preview-state]').forEach(button => button.addEventListener('click', () => {
    root.querySelectorAll('[data-room-ui-preview-state]').forEach(b => b.classList.toggle('active', b === button));
    preview.dataset.previewState = button.dataset.roomUiPreviewState;
    const demo = preview.querySelector('[data-rui-state-demo]');
    if (demo) demo.textContent = stateLabels[button.dataset.roomUiPreviewState] || 'CHỜ ĐỐI THỦ';
    fitWholePreview();
  }));

  window.addEventListener('resize', fitWholePreview);
  if ('ResizeObserver' in window && preview) new ResizeObserver(fitWholePreview).observe(preview);
  fitWholePreview();

  root.querySelector('[data-room-ui-zero-y]')?.addEventListener('click', () => {
    const yKeys = new Set(['player_panel_y','center_y','sidebar_y','brand_y','avatar_y','player_name_y','club_area_y','active_mode_logo_y','vs_y']);
    inputs.forEach(input => { if (yKeys.has(input.dataset.roomUiInput)) { input.value = '0'; apply(input); } });
  });
})();
