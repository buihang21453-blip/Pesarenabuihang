(() => {
  const root = document.querySelector('[data-room-ui-designer]');
  if (!root) return;
  const preview = root.querySelector('[data-room-ui-preview]');
  const inputs = [...root.querySelectorAll('[data-room-ui-input]')];
  const cssMap = {
    host_width:'--p-host', center_width:'--p-center', opponent_width:'--p-away', sidebar_width:'--p-side',
    main_height:'--p-height', main_gap:'--p-main-gap', mode_gap:'--p-mode-gap',
    host_x:'--p-host-x', host_y:'--p-host-y', center_x:'--p-center-x', center_y:'--p-center-y',
    opponent_x:'--p-away-x', opponent_y:'--p-away-y', sidebar_x:'--p-side-x', sidebar_y:'--p-side-y',
    brand_scale:'--p-brand-scale', brand_x:'--p-brand-x', brand_y:'--p-brand-y',
    avatar_scale:'--p-avatar-scale', avatar_x:'--p-avatar-x', avatar_y:'--p-avatar-y',
    player_name_scale:'--p-name-scale', player_name_x:'--p-name-x', player_name_y:'--p-name-y',
    active_mode_logo_scale:'--p-active-scale', active_mode_logo_x:'--p-active-x', active_mode_logo_y:'--p-active-y',
    vs_scale:'--p-vs-scale', vs_x:'--p-vs-x', vs_y:'--p-vs-y',
    mode_logo_scale:'--p-mode-scale', mode_card_height:'--p-card-height', mode_status_width:'--p-status-width',
    panel_opacity:'--p-opacity', gold_glow:'--p-glow'
  };
  const pxUnits = new Set(['main_height','main_gap','mode_gap','host_x','host_y','center_x','center_y','opponent_x','opponent_y','sidebar_x','sidebar_y','brand_x','brand_y','avatar_x','avatar_y','player_name_x','player_name_y','active_mode_logo_x','active_mode_logo_y','vs_x','vs_y','mode_card_height']);
  const frUnits = new Set(['host_width','center_width','opponent_width','sidebar_width']);
  const byKey = key => root.querySelector(`[data-room-ui-input="${key}"]`);

  function apply(input) {
    const key = input.dataset.roomUiInput;
    const value = input.value;
    const output = root.querySelector(`[data-output-for="${key}"]`);
    if (output) output.value = value;
    if (!preview || !cssMap[key]) return;
    let suffix = pxUnits.has(key) ? 'px' : '';
    if (frUnits.has(key)) suffix = 'fr';
    if (key === 'mode_status_width') suffix = '%';
    preview.style.setProperty(cssMap[key], `${value}${suffix}`);
  }
  inputs.forEach(input => { apply(input); input.addEventListener('input', () => apply(input)); });

  [...root.querySelectorAll('[data-drag-object]')].forEach(el => {
    el.addEventListener('pointerdown', event => {
      const xInput = byKey(el.dataset.dragXKey), yInput = byKey(el.dataset.dragYKey);
      if (!xInput || !yInput) return;
      event.preventDefault(); event.stopPropagation();
      el.setPointerCapture?.(event.pointerId); el.classList.add('is-dragging');
      const startX = event.clientX, startY = event.clientY;
      const baseX = Number(xInput.value || 0), baseY = Number(yInput.value || 0), factor = 1.6;
      const clamp = (value, input) => Math.max(Number(input.min), Math.min(Number(input.max), value));
      const move = ev => {
        xInput.value = Math.round(clamp(baseX + (ev.clientX-startX)*factor, xInput));
        yInput.value = Math.round(clamp(baseY + (ev.clientY-startY)*factor, yInput));
        apply(xInput); apply(yInput);
      };
      const up = () => { el.classList.remove('is-dragging'); window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
      window.addEventListener('pointermove', move); window.addEventListener('pointerup', up, {once:true});
    });
  });

  const stateLabels = {
    waiting:'CHỜ ĐỐI THỦ', ready:'CHỜ SẴN SÀNG', playing:'ĐANG THI ĐẤU',
    confirm:'CHỜ XÁC NHẬN KẾT QUẢ', confirmed:'ĐÃ XÁC NHẬN', rematch:'ĐÁ TIẾP / THOÁT PHÒNG'
  };
  root.querySelectorAll('[data-room-ui-preview-state]').forEach(button => {
    button.addEventListener('click', () => {
      root.querySelectorAll('[data-room-ui-preview-state]').forEach(b => b.classList.toggle('active', b === button));
      const key = button.dataset.roomUiPreviewState;
      preview?.setAttribute('data-preview-state', key);
      const demo = root.querySelector('[data-rui-state-demo]');
      if (demo) demo.textContent = stateLabels[key] || key;
    });
  });

  root.querySelector('[data-room-ui-zero-offsets]')?.addEventListener('click', () => {
    inputs.filter(i => /_(x|y)$/.test(i.dataset.roomUiInput || '')).forEach(i => { i.value=0; apply(i); });
  });
})();
