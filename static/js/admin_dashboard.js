(function () {
    'use strict';

    const buttons = Array.from(document.querySelectorAll('[data-admin-tab]'));
    const currentPanel = document.querySelector('[data-admin-panel]');
    const activeTab = currentPanel ? currentPanel.dataset.adminPanel : 'overview';

    buttons.forEach((button) => {
        const isActive = button.dataset.adminTab === activeTab;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-selected', isActive ? 'true' : 'false');
        button.tabIndex = isActive ? 0 : -1;
    });

    // Mỗi tab Admin là một module tải riêng từ server. Không còn dựng toàn bộ
    // admin.html và toàn bộ dữ liệu của mọi tab trong một request.
    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-admin-tab]');
        if (!button) return;
        event.preventDefault();
        const targetUrl = button.dataset.adminUrl;
        if (!targetUrl || button.dataset.adminTab === activeTab) return;
        button.classList.add('is-loading');
        button.setAttribute('aria-busy', 'true');
        window.location.assign(targetUrl);
    });

    const searchInput = document.getElementById('adminUserSearch');
    const duplicateOnly = document.getElementById('adminDuplicateOnly');
    const userRows = Array.from(document.querySelectorAll('[data-user-summary]'));
    const emptyState = document.getElementById('adminUserEmpty');
    let filterFrame = null;

    function applyUserFilters() {
        filterFrame = null;
        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const onlyDuplicate = Boolean(duplicateOnly && duplicateOnly.checked);
        let visible = 0;

        userRows.forEach((row) => {
            const matchesQuery = !query || (row.dataset.userSearch || '').includes(query);
            const matchesDuplicate = !onlyDuplicate || row.dataset.duplicateIp === '1';
            const shouldShow = matchesQuery && matchesDuplicate;
            const toggle = row.querySelector('[data-user-toggle]');
            const detail = toggle ? document.getElementById(toggle.dataset.userToggle) : null;
            row.hidden = !shouldShow;
            if (!shouldShow && detail) {
                detail.hidden = true;
                toggle.setAttribute('aria-expanded', 'false');
                toggle.textContent = 'Quản lý';
            }
            if (shouldShow) visible += 1;
        });
        if (emptyState) emptyState.hidden = visible !== 0;
    }

    function queueUserFilter() {
        if (filterFrame) cancelAnimationFrame(filterFrame);
        filterFrame = requestAnimationFrame(applyUserFilters);
    }

    if (searchInput) searchInput.addEventListener('input', queueUserFilter, { passive: true });
    if (duplicateOnly) duplicateOnly.addEventListener('change', applyUserFilters);

    document.addEventListener('click', (event) => {
        const toggle = event.target.closest('[data-user-toggle]');
        if (!toggle) return;
        const detail = document.getElementById(toggle.dataset.userToggle);
        if (!detail) return;
        const opening = detail.hidden;
        detail.hidden = !opening;
        toggle.setAttribute('aria-expanded', opening ? 'true' : 'false');
        toggle.textContent = opening ? 'Đóng' : 'Quản lý';
        if (opening) requestAnimationFrame(() => detail.scrollIntoView({ block: 'nearest', behavior: 'smooth' }));
    });

    const showPasswords = document.getElementById('showAdminPasswords');
    if (showPasswords) {
        showPasswords.addEventListener('change', () => {
            document.querySelectorAll('.admin-new-password').forEach((input) => {
                input.type = showPasswords.checked ? 'text' : 'password';
            });
        });
    }

    document.querySelectorAll('.temporary-password-input').forEach((input) => {
        input.addEventListener('focus', () => { input.type = 'text'; });
        input.addEventListener('blur', () => { input.type = 'password'; });
    });

    document.querySelectorAll('.admin-report-filter a').forEach((link) => {
        link.addEventListener('click', () => {
            link.classList.add('is-loading');
            link.setAttribute('aria-busy', 'true');
        });
    });
})();
