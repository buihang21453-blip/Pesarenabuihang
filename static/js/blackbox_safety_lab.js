(function BlackBoxSafetyLab(){
  'use strict';
  const cfg = window.PES_BLACKBOX_SAFETY_CONFIG || {};
  const btn = document.getElementById('bbRunSafety');
  if (!btn) return;
  const rowsEl = document.getElementById('bbSafetyRows');
  const overallEl = document.getElementById('bbSafetyOverall');
  const summaryEl = document.getElementById('bbSafetySummary');
  const exportBtn = document.getElementById('bbExportSafety');
  let lastReport = null;

  function esc(v){
    return String(v == null ? '' : v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  }
  function statusClass(s){
    return s === 'PASS' ? 'success' : (s === 'FAIL' ? 'danger' : 'warning');
  }
  function item(group, name, status, detail, extra){
    return {group, name, status, detail, ...(extra || {})};
  }

  function uiLayer(el){
    if (!el || !el.closest) return 'page';
    if (el.closest('.player-topbar')) return 'topbar';
    if (el.closest('.topbar-account-dropdown, .notification-panel, [role="dialog"], .modal, .dropdown-menu')) return 'overlay';
    return 'page';
  }

  function scanOverlaps(){
    const selectors = 'button,a,.btn,[role="button"],input[type="submit"],input[type="button"],select';
    const els = Array.from(document.querySelectorAll(selectors)).filter(el => {
      const r = el.getBoundingClientRect();
      const st = getComputedStyle(el);
      if (!(r.width > 4 && r.height > 4 && st.display !== 'none' && st.visibility !== 'hidden' && Number(st.opacity || 1) > 0)) return false;
      // Ignore controls fully outside the visible viewport. Hidden/off-screen tab content
      // can otherwise create false overlap warnings after content-visibility/layout containment.
      if (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth) return false;
      return true;
    });
    const collisions = [];
    const maxPairs = 12000;
    let pairs = 0;
    for (let i=0; i<els.length; i++) {
      const a = els[i], ar = a.getBoundingClientRect();
      for (let j=i+1; j<els.length; j++) {
        if (++pairs > maxPairs) break;
        const b = els[j];
        if (a.contains(b) || b.contains(a)) continue;
        // Sticky topbar, dropdowns/modals and normal page content are separate UI layers.
        // Cross-layer overlap is intentional (content scrolls underneath overlays/header),
        // so only report collisions between controls in the same interaction layer.
        if (uiLayer(a) !== uiLayer(b)) continue;
        const br = b.getBoundingClientRect();
        const iw = Math.max(0, Math.min(ar.right, br.right) - Math.max(ar.left, br.left));
        const ih = Math.max(0, Math.min(ar.bottom, br.bottom) - Math.max(ar.top, br.top));
        if (!iw || !ih) continue;
        const inter = iw * ih;
        const minArea = Math.max(1, Math.min(ar.width*ar.height, br.width*br.height));
        const ratio = inter / minArea;
        if (ratio >= 0.18) {
          collisions.push({
            a: a.id ? '#'+a.id : (a.className ? String(a.className).slice(0,90) : a.tagName),
            b: b.id ? '#'+b.id : (b.className ? String(b.className).slice(0,90) : b.tagName),
            ratio: Number(ratio.toFixed(2))
          });
          if (collisions.length >= 20) return collisions;
        }
      }
      if (pairs > maxPairs) break;
    }
    return collisions;
  }

  function browserChecks(){
    const out = [];
    const bb = window.PESBlackBox;
    if (cfg.blackboxLoaded) {
      if (bb && typeof bb.getDiagnostics === 'function') {
        const d = bb.getDiagnostics();
        out.push(item('Browser', 'Black Box runtime', 'PASS', 'Runtime đã nạp; buffer='+d.bufferLength+'/'+d.maxBuffer+', batch='+d.batchSize+', flush='+d.flushMs+'ms.'));
        const bench = typeof bb.microBenchmark === 'function' ? bb.microBenchmark(5000) : null;
        if (bench) {
          const status = bench.perOperationMs <= 0.1 ? 'PASS' : 'WARNING';
          out.push(item('Performance', 'Micro benchmark 5.000 operations', status, bench.totalMs+'ms tổng; '+bench.perOperationMs+'ms/op.', {benchmark:bench}));
        }
      } else {
        out.push(item('Browser', 'Black Box runtime', 'FAIL', 'Cấu hình yêu cầu bật nhưng PESBlackBox không tồn tại.'));
      }
    } else {
      out.push(item('Browser', 'Kill Switch frontend', bb ? 'FAIL' : 'PASS', bb ? 'Black Box vẫn được nạp dù config đang OFF.' : 'OFF thật: không có runtime/listener/timer Black Box.'));
    }

    const t0 = performance.now();
    const overlaps = scanOverlaps();
    const scanMs = performance.now() - t0;
    out.push(item('UI/CSS', 'Interactive overlap scan', overlaps.length ? 'WARNING' : 'PASS', overlaps.length ? ('Phát hiện '+overlaps.length+' cặp có thể chồng nhau trên trang Admin hiện tại.') : ('Không thấy va chạm đáng kể; scan '+scanMs.toFixed(1)+'ms.'), {overlaps}));

    const nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    if (nav) {
      const domMs = Math.max(0, nav.domContentLoadedEventEnd - nav.startTime);
      out.push(item('Performance', 'DOM Content Loaded', domMs < 2500 ? 'PASS' : 'WARNING', Math.round(domMs)+'ms trên thiết bị/trình duyệt hiện tại.'));
    } else {
      out.push(item('Performance', 'DOM Content Loaded', 'NOT_TESTED', 'Navigation Timing không khả dụng.'));
    }
    out.push(item('Gameplay', 'Luồng 2 người / RP end-to-end', 'NOT_TESTED', 'Không chạy trên production để tránh tạo phòng/trận/RP giả.'));
    return out;
  }

  function render(report){
    const checks = report.checks || [];
    rowsEl.innerHTML = checks.map(x => '<tr><td>'+esc(x.group || 'Server')+'</td><td>'+esc(x.name)+'</td><td><span class="status-badge '+statusClass(x.status)+'">'+esc(x.status)+'</span></td><td>'+esc(x.detail)+'</td></tr>').join('');
    const counts = ['PASS','WARNING','FAIL','NOT_TESTED'].reduce((a,k) => (a[k]=checks.filter(x=>x.status===k).length,a),{});
    summaryEl.style.display = '';
    summaryEl.innerHTML = ['PASS','WARNING','FAIL','NOT_TESTED'].map(k => '<article class="admin-metric-card"><div><span>'+k+'</span><strong>'+counts[k]+'</strong></div></article>').join('');
    const overall = counts.FAIL ? 'FAIL' : ((counts.WARNING || counts.NOT_TESTED) ? 'WARNING' : 'PASS');
    overallEl.textContent = overall;
    overallEl.className = 'status-badge '+statusClass(overall);
  }

  async function run(){
    btn.disabled = true;
    exportBtn.disabled = true;
    btn.textContent = '⏳ Đang kiểm tra...';
    rowsEl.innerHTML = '<tr><td colspan="4">Đang chạy kiểm tra server và browser...</td></tr>';
    try {
      const started = new Date().toISOString();
      const res = await fetch(cfg.endpoint, {
        credentials:'same-origin',
        cache:'no-store',
        headers:{'Accept':'application/json','X-PES-Safety-Lab':'1'}
      });
      const contentType = String(res.headers.get('content-type') || '').toLowerCase();
      const raw = await res.text();
      let data = null;
      if (contentType.includes('application/json')) {
        try { data = JSON.parse(raw); } catch (parseError) {
          throw new Error('Safety API trả JSON lỗi cú pháp (HTTP '+res.status+').');
        }
      } else {
        const preview = raw.replace(/\s+/g,' ').slice(0,120);
        const redirected = res.redirected ? ('; redirected='+res.url) : '';
        throw new Error('Safety API trả '+(contentType || 'non-JSON')+' HTTP '+res.status+redirected+'. Preview: '+preview);
      }
      const server = data && data.report && Array.isArray(data.report.checks)
        ? data.report.checks.map(x => ({group:'Server', ...x}))
        : [item('Server','Safety API','FAIL','Không nhận được report hợp lệ (HTTP '+res.status+').')];
      const browser = browserChecks();
      lastReport = {
        generated_at: new Date().toISOString(),
        started_at: started,
        app_version: cfg.appVersion,
        page: location.href,
        user_agent: navigator.userAgent,
        viewport: {width:innerWidth,height:innerHeight},
        checks: server.concat(browser)
      };
      render(lastReport);
      exportBtn.disabled = false;
    } catch (err) {
      lastReport = {generated_at:new Date().toISOString(), app_version:cfg.appVersion, checks:[item('Server','Safety API','FAIL',String(err && err.message || err))].concat(browserChecks())};
      render(lastReport);
      exportBtn.disabled = false;
    } finally {
      btn.disabled = false;
      btn.textContent = '▶ Chạy lại kiểm tra tự động';
    }
  }

  btn.addEventListener('click', run);
  exportBtn.addEventListener('click', function(){
    if (!lastReport) return;
    const blob = new Blob([JSON.stringify(lastReport,null,2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'PES_Arena_BlackBox_Safety_'+String(cfg.appVersion || 'unknown').replace(/[^0-9A-Za-z._-]/g,'_')+'.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
})();
