(function () {
    const buttons = Array.from(document.querySelectorAll('[data-admin-tab]'));
    const panels = Array.from(document.querySelectorAll('[data-admin-panel]'));
    const allowedTabs = new Set(buttons.map(function (button) { return button.dataset.adminTab; }));

    function activateAdminTab(tabName) {
        const selected = allowedTabs.has(tabName) ? tabName : 'overview';
        buttons.forEach(function (button) {
            const active = button.dataset.adminTab === selected;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        panels.forEach(function (panel) {
            panel.hidden = panel.dataset.adminPanel !== selected;
        });
    }

    buttons.forEach(function (button) {
        button.addEventListener('click', function () {
            const tabName = button.dataset.adminTab;
            window.location.hash = tabName;
            activateAdminTab(tabName);
        });
    });

    // Giữ nguyên tab hiện tại sau khi lưu bất kỳ cài đặt Admin nào.
    document.querySelectorAll('.admin-tab-panel form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const panel = form.closest('[data-admin-panel]');
            if (!panel) return;
            let input = form.querySelector('input[name="_admin_tab"]');
            if (!input) {
                input = document.createElement('input');
                input.type = 'hidden';
                input.name = '_admin_tab';
                form.appendChild(input);
            }
            input.value = panel.dataset.adminPanel || 'overview';
        });
    });

    window.addEventListener('hashchange', function () {
        activateAdminTab(window.location.hash.replace('#', ''));
    });
    activateAdminTab(window.location.hash.replace('#', ''));

    const searchInput = document.getElementById('adminUserSearch');
    const duplicateOnly = document.getElementById('adminDuplicateOnly');
    const userRows = Array.from(document.querySelectorAll('[data-user-summary]'));
    const emptyState = document.getElementById('adminUserEmpty');

    function applyUserFilters() {
        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const onlyDuplicate = duplicateOnly ? duplicateOnly.checked : false;
        let visible = 0;

        userRows.forEach(function (row) {
            const matchesQuery = !query || (row.dataset.userSearch || '').includes(query);
            const matchesDuplicate = !onlyDuplicate || row.dataset.duplicateIp === '1';
            const shouldShow = matchesQuery && matchesDuplicate;
            const button = row.querySelector('[data-user-toggle]');
            const detail = button ? document.getElementById(button.dataset.userToggle) : null;

            row.hidden = !shouldShow;
            if (!shouldShow && detail) {
                detail.hidden = true;
                button.setAttribute('aria-expanded', 'false');
                button.textContent = 'Quản lý';
            }
            if (shouldShow) visible += 1;
        });

        if (emptyState) emptyState.hidden = visible !== 0;
    }

    if (searchInput) searchInput.addEventListener('input', applyUserFilters);
    if (duplicateOnly) duplicateOnly.addEventListener('change', applyUserFilters);

    document.querySelectorAll('[data-user-toggle]').forEach(function (button) {
        button.addEventListener('click', function () {
            const detail = document.getElementById(button.dataset.userToggle);
            if (!detail) return;
            const opening = detail.hidden;
            detail.hidden = !opening;
            button.setAttribute('aria-expanded', opening ? 'true' : 'false');
            button.textContent = opening ? 'Đóng' : 'Quản lý';
        });
    });

    const showPasswords = document.getElementById('showAdminPasswords');
    if (showPasswords) {
        showPasswords.addEventListener('change', function () {
            document.querySelectorAll('.admin-new-password').forEach(function (input) {
                input.type = showPasswords.checked ? 'text' : 'password';
            });
        });
    }

    document.querySelectorAll('.temporary-password-input').forEach(function (input) {
        input.addEventListener('focus', function () { input.type = 'text'; });
        input.addEventListener('blur', function () { input.type = 'password'; });
    });

    document.querySelectorAll('.admin-permission-form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const button = form.querySelector('.admin-save-permissions');
            if (!button || button.disabled) return;
            button.disabled = true;
            button.classList.add('is-saving');
            const label = button.querySelector('.admin-save-label');
            if (label) label.textContent = 'Đang lưu...';
        });
    });
})();

(function () {
    function loadLazyModule(tabName) {
        const panel = document.querySelector('[data-admin-panel="' + tabName + '"]');
        if (!panel) return;
        panel.querySelectorAll('iframe[data-admin-lazy-src]').forEach(function (frame) {
            if (frame.src) return;
            frame.src = frame.dataset.adminLazySrc;
        });
    }
    document.querySelectorAll('[data-admin-tab]').forEach(function (button) {
        button.addEventListener('click', function () { loadLazyModule(button.dataset.adminTab); });
    });
    loadLazyModule(window.location.hash.replace('#', ''));
})();


// PES Arena V1.3.15 — Preview trực tiếp cho tab Thiết kế phòng đấu.
(function () {
    const preview = document.getElementById('adminRoomPreview');
    if (!preview) return;

    const designTab = document.querySelector('[data-admin-panel="room-design"]');
    if (!designTab) return;

    const initial = {
        style: preview.dataset.roomStyle || 'default',
        bars: preview.dataset.centerBars || 'visible',
        layout: preview.dataset.centerLayout || 'compact',
        cssText: preview.getAttribute('style') || ''
    };

    function numberValue(name, fallback) {
        const el = designTab.querySelector('[name="' + name + '"]');
        const value = el ? Number(el.value) : fallback;
        return Number.isFinite(value) ? value : fallback;
    }

    function syncPreview() {
        const bars = designTab.querySelector('[name="center_bars_visible"]');
        const layout = designTab.querySelector('[name="vertical_layout"]');
        const style = designTab.querySelector('[name="room_visual_style"]:checked');
        const quickColor = designTab.querySelector('[name="color"]');

        preview.dataset.centerBars = bars && bars.checked ? 'visible' : 'hidden';
        preview.dataset.centerLayout = layout ? layout.value : 'compact';
        preview.dataset.roomStyle = style ? style.value : (preview.dataset.roomStyle || 'default');

        preview.style.setProperty('--preview-panel-height', numberValue('panel_height', 600) + 'px');
        preview.style.setProperty('--preview-stage-padding', numberValue('stage_padding', 18) + 'px');
        preview.style.setProperty('--preview-stage-gap', numberValue('stage_gap', 18) + 'px');
        preview.style.setProperty('--preview-mode-width', numberValue('mode_width', 320) + 'px');
        preview.style.setProperty('--preview-mode-padding', numberValue('mode_padding', 13) + 'px');
        preview.style.setProperty('--preview-vs-size', numberValue('vs_size', 150) + 'px');
        preview.style.setProperty('--preview-score-width', numberValue('score_width', 340) + 'px');
        preview.style.setProperty('--preview-score-padding', numberValue('score_padding', 14) + 'px');
        preview.style.setProperty('--preview-score-input-height', numberValue('score_input_height', 44) + 'px');
        preview.style.setProperty('--preview-action-height', numberValue('action_height', 46) + 'px');
        preview.style.setProperty('--preview-logo-bg-opacity', numberValue('room_mode_logo_background_opacity', 0) / 100);
        preview.style.setProperty('--preview-center-logo-scale', numberValue('room_mode_logo_scale', 100) / 100);
        preview.style.setProperty('--preview-dock-logo-scale', numberValue('room_mode_dock_logo_scale', 135) / 100);

        const actionButton = preview.querySelector('.admin-room-preview-score .btn');
        if (actionButton && quickColor) {
            actionButton.classList.toggle('green', quickColor.value === 'green');
            actionButton.classList.toggle('blue', quickColor.value === 'blue');
        }
    }

    designTab.querySelectorAll('input, select').forEach(function (control) {
        control.addEventListener('input', syncPreview);
        control.addEventListener('change', syncPreview);
    });

    const reset = document.getElementById('adminRoomPreviewReset');
    if (reset) {
        reset.addEventListener('click', function () {
            preview.setAttribute('style', initial.cssText);
            preview.dataset.roomStyle = initial.style;
            preview.dataset.centerBars = initial.bars;
            preview.dataset.centerLayout = initial.layout;
            designTab.querySelectorAll('form').forEach(function (form) { form.reset(); });
            syncPreview();
        });
    }

    syncPreview();
})();
