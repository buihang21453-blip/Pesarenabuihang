(function(){
  function activate(phase){
    document.querySelectorAll('[data-phase-panel]').forEach(function(panel){panel.classList.toggle('active',panel.dataset.phasePanel===phase);});
    document.querySelectorAll('[data-preview-phase]').forEach(function(btn){btn.classList.toggle('active',btn.dataset.previewPhase===phase);});
  }
  document.addEventListener('click',function(e){
    var phaseBtn=e.target.closest('[data-preview-phase]');
    if(phaseBtn){activate(phaseBtn.dataset.previewPhase);return;}
    if(e.target.closest('[data-preview-fullscreen]')){
      if(!document.fullscreenElement){document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();}
      else{document.exitFullscreen&&document.exitFullscreen();}
    }
  });
  function fmtVN(iso){
    var d=new Date(iso); if(isNaN(d.getTime())) return '—';
    return new Intl.DateTimeFormat('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric',hourCycle:'h23'}).format(d).replace(',', ' ·');
  }
  var body=document.body;
  var deadlineLabel=document.querySelector('[data-preview-deadline-label]');
  var startLabel=document.querySelector('[data-preview-start-label]');
  if(deadlineLabel)deadlineLabel.textContent=fmtVN(body.dataset.rewardDeadline);
  if(startLabel)startLabel.textContent=fmtVN(body.dataset.leagueStart);
  function tick(){
    var now=Date.now(), draw=Date.parse(body.dataset.drawAt||''), reward=Date.parse(body.dataset.rewardDeadline||''), league=Date.parse(body.dataset.leagueStart||'');
    var target=draw, caption='Đếm ngược đến lễ bốc thăm';
    if(isFinite(draw)&&now>=draw){target=reward;caption='Còn thời gian dùng vé thưởng';}
    if(isFinite(reward)&&now>=reward){target=league;caption='Đếm ngược đến mốc mở GĐ2';}
    var el=document.querySelector('[data-preview-clock]'), cap=document.querySelector('[data-preview-clock-caption]');
    if(cap)cap.textContent=caption;
    if(!el||!isFinite(target)){return;}
    var ms=Math.max(0,target-now), sec=Math.floor(ms/1000), d=Math.floor(sec/86400), h=Math.floor((sec%86400)/3600), m=Math.floor((sec%3600)/60), s=sec%60;
    el.textContent=(d?d+'d ':'')+String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
  }
  tick();setInterval(tick,1000);
})();
