(() => {
  const root = document.querySelector('[data-room-ui-designer]');
  if (!root) return;
  const preview = root.querySelector('[data-room-ui-preview]');
  const inputs = [...root.querySelectorAll('[data-room-ui-input]')];
  const cssMap = {
    host_width: '--p-host', center_width: '--p-center', opponent_width: '--p-away', sidebar_width: '--p-side',
    main_height: '--p-height', active_mode_logo_scale: '--p-active-scale', vs_scale: '--p-vs-scale',
    mode_card_height: '--p-card-height', mode_status_width: '--p-status-width', panel_opacity: '--p-opacity', gold_glow: '--p-glow',
    mode_1_logo_scale: '--p-mode-1', mode_2_logo_scale: '--p-mode-2', mode_3_logo_scale: '--p-mode-3',
    mode_4_logo_scale: '--p-mode-4', mode_5_logo_scale: '--p-mode-5', mode_6_logo_scale: '--p-mode-6'
  };
  const unit = { main_height: 'px', mode_card_height: 'px', mode_status_width: '%' };

  function apply(input) {
    const key = input.dataset.roomUiInput;
    const value = input.value;
    const output = root.querySelector(`[data-output-for="${key}"]`);
    if (output) output.value = value;
    if (preview && cssMap[key]) preview.style.setProperty(cssMap[key], `${value}${unit[key] || ''}`);
  }
  inputs.forEach(input => {
    apply(input);
    input.addEventListener('input', () => apply(input));
  });

  const sync = root.querySelector('[data-room-ui-sync]');
  if (sync) sync.addEventListener('click', () => {
    const source = root.querySelector('[data-room-ui-input="mode_1_logo_scale"]');
    if (!source) return;
    root.querySelectorAll('[data-mode-scale]').forEach(input => {
      input.value = source.value;
      apply(input);
    });
  });
})();
