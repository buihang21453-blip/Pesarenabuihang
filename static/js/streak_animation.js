(() => {
  "use strict";
  const ICONS = {
    fire: '<svg viewBox="0 0 64 64"><path d="M34 4c3 12-5 16 1 25 4-8 11-10 13-19 8 11 12 21 10 31-3 14-14 21-27 20C16 60 6 50 7 36 8 25 17 18 24 10c0 10 2 15 7 18-2-10 6-14 3-24z"/></svg>',
    trophy: '<svg viewBox="0 0 64 64"><path d="M19 8h26v8h10v8c0 10-7 17-17 19v7h10v7H16v-7h10v-7C16 41 9 34 9 24v-8h10V8zm0 15h-4v2c0 5 3 9 8 11-2-4-4-8-4-13zm26 0c0 5-2 9-4 13 5-2 8-6 8-11v-2h-4z"/></svg>',
    skull: '<svg viewBox="0 0 64 64"><path d="M32 5C17 5 8 14 8 28c0 10 5 17 13 20v9h8v-7h6v7h8v-9c8-3 13-10 13-20C56 14 47 5 32 5zm-11 28c-5 0-8-3-8-7 0-4 3-7 8-7s8 3 8 7c0 4-3 7-8 7zm22 0c-5 0-8-3-8-7 0-4 3-7 8-7s8 3 8 7c0 4-3 7-8 7zM28 40l4-5 4 5-4 5-4-5z"/></svg>',
    crown: '<svg viewBox="0 0 64 64"><path d="M8 18l14 10 10-19 10 19 14-10-6 31H14L8 18zm8 36h32v6H16v-6z"/></svg>',
    bolt: '<svg viewBox="0 0 64 64"><path d="M35 2L12 36h17l-3 26 26-38H35V2z"/></svg>'
  };
  function themeFor(kind, title) {
    const t = String(title || '').toUpperCase();
    if (kind === 'shutdown' || t.includes('SHUTDOWN')) return ['theme-shutdown','bolt'];
    if (t.includes('BEYOND')) return ['theme-beyond','crown'];
    if (t.includes('GODLIKE')) return ['theme-godlike','trophy'];
    if (t.includes('MONSTER')) return ['theme-monster','fire'];
    if (t.includes('TERMINATOR')) return ['theme-terminator','skull'];
    if (t.includes('UNSTOPPABLE')) return ['theme-unstoppable','fire'];
    if (t.includes('POKER')) return ['theme-poker','fire'];
    return ['theme-default','fire'];
  }
  function esc(v) { const d=document.createElement('div'); d.textContent=String(v||''); return d.innerHTML; }
  function eventSeen(id){ return localStorage.getItem('pes2026-streak-v114:'+id); }
  function markSeen(id){ localStorage.setItem('pes2026-streak-v114:'+id,String(Date.now())); }
  function build(event){
    const id=esc(event.id||('event-'+Date.now()));
    const title=esc(event.title||'');
    const subtitle=esc(event.subtitle||'');
    const kind=esc(event.kind||'milestone');
    const toastTitle=esc(event.toast_title||'THÔNG BÁO HỆ THỐNG');
    const wrap=document.createElement('div');
    wrap.innerHTML=`<div id="winStreakToast" class="streak-toast" data-event-id="${id}" data-kind="${kind}" data-title="${title}" data-duration="${Number(event.toast_duration||6000)}"><div class="streak-toast-mark" aria-hidden="true"><span></span></div><div class="streak-toast-copy"><small>${toastTitle}</small><div><strong>${title}</strong> ${subtitle}</div></div><button type="button" class="streak-toast-close" aria-label="Đóng thông báo">×</button></div><div id="winStreakAnnouncement" class="streak-scene" data-event-id="${id}" data-kind="${kind}" data-title="${title}" data-duration="${Number(event.overlay_duration||4000)}" role="status" aria-live="polite"><div class="streak-dimmer"></div><div class="streak-rays"></div><div class="streak-particles"></div><div class="streak-energy-line left"></div><div class="streak-energy-line right"></div><div class="streak-panel"><div class="streak-panel-edge"></div><div class="streak-scan"></div><div class="streak-icon"></div><strong class="streak-main-title">${title}</strong><span class="streak-main-subtitle">${subtitle}</span></div></div>`;
    document.body.append(...wrap.children);
  }
  function play(scene,toast,eventId){
    const source=scene||toast;if(!source)return;
    const [theme,icon]=themeFor(source.dataset.kind,source.dataset.title);
    [scene,toast].forEach(el=>el&&el.classList.add(theme));
    if(scene){const duration=Math.max(2800,Number(scene.dataset.duration||4000));scene.style.setProperty('--scene-time',duration+'ms');const box=scene.querySelector('.streak-icon');if(box)box.innerHTML=ICONS[icon]||ICONS.fire;requestAnimationFrame(()=>scene.classList.add('is-active'));setTimeout(()=>scene.remove(),duration+250);}
    if(toast){const duration=Math.max(3500,Number(toast.dataset.duration||6000));toast.querySelector('.streak-toast-close')?.addEventListener('click',()=>toast.remove());requestAnimationFrame(()=>toast.classList.add('is-active'));setTimeout(()=>{toast.classList.add('is-leaving');setTimeout(()=>toast.remove(),450)},duration-450);}
    markSeen(eventId);
  }
  function show(event){
    if(!event||!event.id||eventSeen(event.id))return;
    document.getElementById('winStreakAnnouncement')?.remove();
    document.getElementById('winStreakToast')?.remove();
    build(event);
    play(document.getElementById('winStreakAnnouncement'),document.getElementById('winStreakToast'),event.id);
  }
  function init(){
    const scene=document.getElementById('winStreakAnnouncement');
    const toast=document.getElementById('winStreakToast');
    const source=scene||toast;if(!source)return;
    const id=source.dataset.eventId||('initial-'+Date.now());
    if(eventSeen(id)){scene?.remove();toast?.remove();return;}
    play(scene,toast,id);
  }
  window.PESStreakAnimation={show};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
