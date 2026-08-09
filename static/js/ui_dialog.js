(function () {
    'use strict';

    const queue = [];
    let active = false;

    function ensureRoot() {
        let root = document.getElementById('appUiDialog');
        if (root) return root;
        root = document.createElement('div');
        root.id = 'appUiDialog';
        root.className = 'app-ui-dialog';
        root.hidden = true;
        root.innerHTML = `
          <div class="app-ui-dialog-backdrop" data-ui-dialog-cancel></div>
          <section class="app-ui-dialog-card" role="dialog" aria-modal="true" aria-labelledby="appUiDialogTitle">
            <button class="app-ui-dialog-close" type="button" data-ui-dialog-cancel aria-label="Đóng">×</button>
            <div class="app-ui-dialog-icon" aria-hidden="true">⚠</div>
            <div class="app-ui-dialog-copy">
              <span class="app-ui-dialog-kicker">PES ARENA</span>
              <h2 id="appUiDialogTitle">Xác nhận thao tác</h2>
              <p id="appUiDialogMessage"></p>
            </div>
            <div class="app-ui-dialog-actions">
              <button class="btn gray" type="button" data-ui-dialog-cancel>Hủy</button>
              <button class="btn green" type="button" data-ui-dialog-confirm>Xác nhận</button>
            </div>
          </section>`;
        document.body.appendChild(root);
        return root;
    }

    function runNext() {
        if (active || !queue.length) return;
        active = true;
        const item = queue.shift();
        const root = ensureRoot();
        const title = root.querySelector('#appUiDialogTitle');
        const message = root.querySelector('#appUiDialogMessage');
        const icon = root.querySelector('.app-ui-dialog-icon');
        const confirmButton = root.querySelector('[data-ui-dialog-confirm]');
        title.textContent = item.options.title || 'Xác nhận thao tác';
        message.textContent = item.message || '';
        icon.textContent = item.options.icon || '⚠';
        confirmButton.textContent = item.options.confirmLabel || 'Xác nhận';
        const tone = ['success', 'danger', 'warning', 'info'].includes(item.options.tone) ? item.options.tone : 'success';
        root.classList.remove('tone-success', 'tone-danger', 'tone-warning', 'tone-info');
        root.classList.add('tone-' + tone);
        // Keep legacy button classes for compatibility; ui_dialog.css owns the final tone.
        confirmButton.className = 'btn ' + (tone === 'danger' ? 'red' : tone === 'warning' ? 'gold' : tone === 'info' ? 'blue' : 'green');
        root.hidden = false;
        document.body.classList.add('app-ui-dialog-open');

        function finish(value) {
            root.hidden = true;
            document.body.classList.remove('app-ui-dialog-open');
            root.removeEventListener('click', onClick);
            document.removeEventListener('keydown', onKeydown, true);
            active = false;
            item.resolve(value);
            runNext();
        }
        function onClick(event) {
            if (event.target.closest('[data-ui-dialog-confirm]')) finish(true);
            else if (event.target.closest('[data-ui-dialog-cancel]')) finish(false);
        }
        function onKeydown(event) {
            if (event.key === 'Escape') finish(false);
            if (event.key === 'Enter') finish(true);
        }
        root.addEventListener('click', onClick);
        document.addEventListener('keydown', onKeydown, true);
        requestAnimationFrame(() => confirmButton.focus());
    }

    function confirmDialog(message, options) {
        return new Promise((resolve) => {
            queue.push({ message, options: options || {}, resolve });
            runNext();
        });
    }

    function toast(message, tone) {
        let stack = document.getElementById('appToastStack');
        if (!stack) {
            stack = document.createElement('div');
            stack.id = 'appToastStack';
            stack.className = 'app-toast-stack';
            document.body.appendChild(stack);
        }
        const item = document.createElement('div');
        item.className = 'app-toast ' + (tone || 'info');
        item.textContent = String(message || '');
        stack.appendChild(item);
        requestAnimationFrame(() => item.classList.add('show'));
        window.setTimeout(() => {
            item.classList.remove('show');
            window.setTimeout(() => item.remove(), 220);
        }, 3200);
    }

    function extractConfirm(source) {
        if (!source) return '';
        const match = source.match(/confirm\((['"])(.*?)\1\)/s);
        return match ? match[2].replace(/\\'/g, "'").replace(/\\"/g, '"') : '';
    }

    function prepareLegacyConfirms(root) {
        const scope = root && root.querySelectorAll ? root : document;
        const forms = [];
        const clickElements = [];
        if (scope.matches && scope.matches('form[onsubmit*="confirm("]')) forms.push(scope);
        if (scope.matches && scope.matches('[onclick*="confirm("]')) clickElements.push(scope);
        forms.push(...scope.querySelectorAll('form[onsubmit*="confirm("]'));
        clickElements.push(...scope.querySelectorAll('[onclick*="confirm("]'));
        forms.forEach((form) => {
            const message = extractConfirm(form.getAttribute('onsubmit'));
            if (message) form.dataset.uiConfirm = message;
            form.removeAttribute('onsubmit');
        });
        clickElements.forEach((element) => {
            const message = extractConfirm(element.getAttribute('onclick'));
            if (message) element.dataset.uiConfirm = message;
            element.removeAttribute('onclick');
        });
    }

    document.addEventListener('submit', function (event) {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        const submitter = event.submitter;
        const message = (submitter && submitter.dataset.uiConfirm) || form.dataset.uiConfirm;
        if (!message || form.dataset.uiConfirmed === '1') {
            delete form.dataset.uiConfirmed;
            return;
        }
        event.preventDefault();
        confirmDialog(message, { tone: /xóa|khóa|hủy|ghi đè|reset|từ chối/i.test(message) ? 'danger' : 'warning' }).then((confirmed) => {
            if (!confirmed) return;
            form.dataset.uiConfirmed = '1';
            if (typeof form.requestSubmit === 'function') form.requestSubmit(submitter || undefined);
            else form.submit();
        });
    }, true);

    function inferToastTone(message) {
        const text = String(message || '').toLowerCase();
        if (/lỗi|thất bại|không thể|error|failed|từ chối/.test(text)) return 'error';
        if (/thành công|đã lưu|đã gửi|hoàn tất|success/.test(text)) return 'success';
        if (/cảnh báo|chú ý|warning|bỏ cuộc|trừ rp/.test(text)) return 'warning';
        return 'info';
    }

    window.PESDialog = {
        confirm: confirmDialog,
        toast,
        notify: function (message, tone) { toast(message, tone || inferToastTone(message)); }
    };

    function startLegacyObserver() {
        prepareLegacyConfirms(document);
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) prepareLegacyConfirms(node);
            }));
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startLegacyObserver, { once: true });
    else startLegacyObserver();
})();
