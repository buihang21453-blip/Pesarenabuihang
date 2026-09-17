(function(){
  var body=document.body;
  var simulation=null;
  try{simulation=JSON.parse((document.getElementById('draw-simulation-data')||{}).textContent||'{}');}catch(e){simulation={};}
  var sim={mode:false,step:0,timer:null,events:[]};
  var clubLogos={};
  try{clubLogos=JSON.parse((document.getElementById('draw-club-logo-data')||{}).textContent||'{}');}catch(e){clubLogos={};}
  function setAvatar(container, name, url){
    if(!container)return;
    container.replaceChildren();
    var initial=document.createElement('span');initial.textContent=(name||'?').charAt(0).toUpperCase();
    if(url && /^(https?:\/\/|\/static\/)/i.test(url)){
      var img=document.createElement('img');img.src=url;img.alt='Ảnh đại diện '+(name||'HLV');
      img.onerror=function(){img.remove();initial.hidden=false;};initial.hidden=true;
      container.append(img);
    }
    container.append(initial);
  }
  function setClubLogo(club){
    var img=document.querySelector('[data-club-reveal-logo]'), placeholder=document.querySelector('[data-club-reveal-icon]');
    if(!img||!placeholder)return;
    var url=clubLogos[String(club||'').trim().toLocaleLowerCase()]||'';
    if(url && /^(https?:\/\/|\/static\/)/i.test(url)){
      img.onerror=function(){img.hidden=true;placeholder.hidden=false;placeholder.textContent='⚽';};
      img.src=url;img.hidden=false;placeholder.hidden=true;
    }else{img.removeAttribute('src');img.hidden=true;placeholder.hidden=false;placeholder.textContent=club?'⚽':'?';}
  }


  function activate(phase){
    document.querySelectorAll('[data-phase-panel]').forEach(function(panel){panel.classList.toggle('active',panel.dataset.phasePanel===phase);});
    document.querySelectorAll('[data-preview-phase]').forEach(function(btn){btn.classList.toggle('active',btn.dataset.previewPhase===phase);});
  }
  function setMode(mode){
    sim.mode=mode==='simulation';
    body.dataset.controlMode=mode;
    document.querySelectorAll('[data-control-select]').forEach(function(btn){btn.classList.toggle('active',btn.dataset.controlSelect===mode);});
    var live=document.querySelector('[data-live-controls]'), demo=document.querySelector('[data-simulation-controls]');
    if(live)live.hidden=sim.mode;
    document.querySelectorAll('[data-live-action]').forEach(function(el){el.hidden=sim.mode;});
    document.querySelectorAll('.draw-sim-primary').forEach(function(el){el.hidden=!sim.mode;});
    if(demo)demo.hidden=!sim.mode;
    var badge=document.querySelector('[data-control-badge]'), sub=document.querySelector('[data-control-subtitle]'), foot=document.querySelector('[data-footer-mode]');
    if(badge)badge.textContent=sim.mode?'GIẢ LẬP AN TOÀN':'ĐIỀU HÀNH THẬT';
    if(sub)sub.textContent=sim.mode?'Không ghi database · Không trừ vé':'Thao tác trực tiếp dữ liệu giải';
    if(foot)foot.textContent=sim.mode?'ADMIN CONTROL · SIMULATION':'ADMIN CONTROL · LIVE';
    if(sim.mode) resetSimulation(); else {stopAuto();setClubLogo(body.dataset.lastClub||'');}
  }
  function fmtVN(iso){
    var d=new Date(iso); if(isNaN(d.getTime())) return '—';
    return new Intl.DateTimeFormat('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit',year:'numeric',hourCycle:'h23'}).format(d).replace(',', ' ·');
  }
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

  function buildEvents(){
    var members=(simulation.members||[]).slice().sort(function(a,b){return (a.seed_no||99)-(b.seed_no||99);});
    var events=[];
    members.slice().reverse().forEach(function(m){events.push({type:'club',member:m,club:(simulation.clubs||{})[m.user_id]||'CLB mô phỏng'});});
    members.slice().sort(function(a,b){return (a.tier-b.tier)||((a.seed_no||99)-(b.seed_no||99));}).forEach(function(m){
      events.push({type:'opponents',member:m,opponents:((simulation.opponents||{})[m.user_id]||[]).slice(0,4)});
    });
    return events;
  }
  function setSimProgress(text){var el=document.querySelector('[data-sim-progress]');if(el)el.textContent=text;}
  function resetSimulation(){
    stopAuto();sim.step=0;sim.events=buildEvents();setSimProgress('Sẵn sàng · '+sim.events.length+' bước');activate('club');
    document.querySelectorAll('[data-club-row]').forEach(function(row){row.classList.remove('sim-done');var cell=row.querySelector('[data-club-cell]');if(cell)cell.textContent='Chờ giả lập';});
    var rn=document.querySelector('[data-club-reveal-name]');if(rn)rn.textContent='CLB BÍ ẨN';setClubLogo('');
    var first=sim.events.find(function(ev){return ev.type==='club';});
    if(first){var m=first.member||{};setAvatar(document.querySelector('[data-club-avatar]'),m.display_name,m.avatar_url);
      var n=document.querySelector('[data-club-name]'),meta=document.querySelector('[data-club-meta]');
      if(n)n.textContent=m.display_name||'HLV';if(meta)meta.textContent='TIER '+m.tier+' · HẠNG '+m.seed_no+' GĐ1';}
    var label=document.querySelector('[data-club-stage-label]');if(label)label.textContent='HLV ĐANG ĐẾN LƯỢT';
  }
  function renderClub(ev){
    activate('club');
    var m=ev.member||{};
    var a=document.querySelector('[data-club-avatar]'), n=document.querySelector('[data-club-name]'), meta=document.querySelector('[data-club-meta]'), rn=document.querySelector('[data-club-reveal-name]'), ri=document.querySelector('[data-club-reveal-icon]'), pot=document.querySelector('[data-club-pot]');
    setAvatar(a,m.display_name,m.avatar_url);if(n)n.textContent=m.display_name||'HLV';if(meta)meta.textContent='TIER '+m.tier+' · HẠNG '+m.seed_no+' GĐ1';
    if(rn)rn.textContent=ev.club;setClubLogo(ev.club);var label=document.querySelector('[data-club-stage-label]');if(label)label.textContent='CLB VỪA ĐƯỢC BỐC';if(pot)pot.textContent='Kết quả giả lập · Pot '+(4-m.tier);
    var row=document.querySelector('[data-club-row="'+m.user_id+'"]');if(row){row.classList.add('sim-done');var cell=row.querySelector('[data-club-cell]');if(cell)cell.textContent=ev.club;}
  }
  function renderOpponents(ev){
    activate('opponent');
    var m=ev.member||{}, a=document.querySelector('[data-opp-avatar]'), n=document.querySelector('[data-opp-name]'), meta=document.querySelector('[data-opp-meta]');
    setAvatar(a,m.display_name,m.avatar_url);if(n)n.textContent=m.display_name||'HLV';if(meta)meta.textContent='TIER '+m.tier+' · HẠNG '+m.seed_no+' GĐ1 · GIẢ LẬP';
    var wrap=document.querySelector('[data-opponent-slots]');
    if(wrap){
      wrap.innerHTML='';
      for(var i=0;i<4;i++){
        var o=(ev.opponents||[])[i];
        var div=document.createElement('div');div.className='opponent-slot '+(o?'revealed':'');
        var label=document.createElement('small');label.textContent='Trận '+(i+1);
        var portrait=document.createElement('span');portrait.className='draw-opponent-avatar';setAvatar(portrait,o?o.display_name:'?',o?o.avatar_url:'');
        var name=document.createElement('strong');name.textContent=o?(o.display_name||'HLV'):'Chưa có';
        var tier=document.createElement('em');tier.textContent=o?('Tier '+o.tier):'—';
        div.append(label,portrait,name,tier);
        wrap.appendChild(div);
      }
    }
  }
  function nextSimulation(){
    if(!sim.mode)return;
    if(!sim.events.length)sim.events=buildEvents();
    if(sim.step>=sim.events.length){setSimProgress('✅ Hoàn tất lễ giả lập');stopAuto();return;}
    var ev=sim.events[sim.step++];
    if(ev.type==='club')renderClub(ev);else renderOpponents(ev);
    var clubDone=Math.min(sim.step,16), oppDone=Math.max(0,sim.step-16);
    setSimProgress((sim.step>=sim.events.length?'✅ Hoàn tất':'Đang chạy')+' · CLB '+clubDone+'/16 · HLV đối thủ '+oppDone+'/16');
  }
  function stopAuto(){if(sim.timer){clearInterval(sim.timer);sim.timer=null;}}
  function runAuto(){
    if(!sim.mode)return;stopAuto();
    if(sim.step>=sim.events.length)resetSimulation();
    nextSimulation();sim.timer=setInterval(function(){nextSimulation();if(sim.step>=sim.events.length)stopAuto();},850);
  }

  // The backend remains the authority; prevent accidental double submits
  // while its response is in flight (without popup dialogs).
  document.querySelectorAll('[data-live-action]').forEach(function(form){
    form.addEventListener('submit',function(){
      var button=form.querySelector('button[type=submit]');
      if(button && !button.disabled){button.disabled=true;button.textContent='Đang xử lý…';}
    });
  });

  document.addEventListener('click',function(e){
    var modeBtn=e.target.closest('[data-control-select]');if(modeBtn){setMode(modeBtn.dataset.controlSelect);return;}
    var phaseBtn=e.target.closest('[data-preview-phase]');if(phaseBtn){activate(phaseBtn.dataset.previewPhase);return;}
    if(e.target.closest('[data-preview-fullscreen]')){if(!document.fullscreenElement){document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen();}else{document.exitFullscreen&&document.exitFullscreen();}return;}
    if(e.target.closest('[data-sim-auto]')){runAuto();return;}
    if(e.target.closest('[data-sim-next]')){nextSimulation();return;}
    if(e.target.closest('[data-sim-reset]')){resetSimulation();return;}
  });

  var deadlineLabel=document.querySelector('[data-preview-deadline-label]');var startLabel=document.querySelector('[data-preview-start-label]');
  if(deadlineLabel)deadlineLabel.textContent=fmtVN(body.dataset.rewardDeadline);if(startLabel)startLabel.textContent=fmtVN(body.dataset.leagueStart);
  tick();setInterval(tick,1000);setMode('live');activate(body.dataset.defaultPhase==='opponent'?'opponent':'club');
})();
