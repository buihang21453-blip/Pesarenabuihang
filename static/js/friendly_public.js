(function () {
  'use strict';
  const POOLS = {
    premier_league:['Arsenal','Aston Villa','Bournemouth','Brentford','Brighton','Burnley','Chelsea','Crystal Palace','Everton','Fulham','Leeds United','Liverpool','Manchester City','Manchester United','Newcastle United','Nottingham Forest','Sunderland','Tottenham Hotspur','West Ham United','Wolverhampton'],
    la_liga:['Athletic Club','Atlético Madrid','Barcelona','Celta Vigo','Elche','Espanyol','Getafe','Girona','Levante','Mallorca','Osasuna','Rayo Vallecano','Real Betis','Real Madrid','Real Oviedo','Real Sociedad','Sevilla','Valencia','Villarreal','Alavés'],
    five_star:[],
    four_star:[],
    club_five_star:['Real Madrid','Barcelona','Liverpool','Arsenal','Manchester City','Paris Saint-Germain','Inter Milan','Bayern Munich'],
    nation_five_star:['Tây Ban Nha','Pháp','Brazil','Anh','Argentina','Bồ Đào Nha','Đức','Hà Lan']
  };
  const LABELS={premier_league:'Ngoại Hạng Anh',la_liga:'La Liga',five_star:'5 Sao',four_star:'4 Sao',club_five_star:'CLB 5★',nation_five_star:'Quốc Gia 5★'};
  const HISTORY_ROUNDS=5;
  const root=document.querySelector('[data-friendly-randomizer]'); if(!root)return;
  const homeTeam=root.querySelector('[data-home-team]'),awayTeam=root.querySelector('[data-away-team]'),modeName=root.querySelector('[data-mode-name]');
  let activeMode='premier_league', pair=['',''];
  let recentRounds=[];

  function randomIndex(max){if(window.crypto&&window.crypto.getRandomValues){const v=new Uint32Array(1);window.crypto.getRandomValues(v);return v[0]%max;}return Math.floor(Math.random()*max);}
  function pick(list){return list.length?list[randomIndex(list.length)]:'---';}
  function blockedTeams(rounds){const blocked=new Set();rounds.forEach(round=>round.forEach(team=>blocked.add(team)));return blocked;}

  // Prefer excluding every team seen in the previous 5 random actions. If a pool is
  // too small to make that mathematically possible, release the oldest action(s)
  // only until enough valid teams remain. Home and away are always different.
  function candidates(pool, needed, additionallyBlocked){
    let rounds=recentRounds.slice();
    const extra=new Set(additionallyBlocked||[]);
    while(true){
      const blocked=blockedTeams(rounds); extra.forEach(team=>blocked.add(team));
      const available=pool.filter(team=>!blocked.has(team));
      if(available.length>=needed || rounds.length===0)return available;
      rounds.shift();
    }
  }
  function remember(teams){
    const clean=Array.from(new Set(teams.filter(Boolean)));
    if(!clean.length)return;
    recentRounds.push(clean);
    if(recentRounds.length>HISTORY_ROUNDS)recentRounds.shift();
  }
  function resetHistory(){recentRounds=[];}

  function drawBoth(){
    const pool=POOLS[activeMode]||[];
    if(pool.length<2){ pair=['Chưa có dữ liệu','Chưa có dữ liệu']; render(); return; }
    let available=candidates(pool,2,[]);
    if(available.length<2)available=pool.slice();
    pair[0]=pick(available);
    const awayChoices=available.filter(team=>team!==pair[0]);
    pair[1]=pick(awayChoices.length?awayChoices:pool.filter(team=>team!==pair[0]));
    remember(pair);
    render();
  }
  function drawOne(side){
    const pool=POOLS[activeMode]||[];
    if(pool.length<2){ pair=['Chưa có dữ liệu','Chưa có dữ liệu']; render(); return; }
    const other=pair[side===0?1:0];
    let available=candidates(pool,1,[other]);
    if(!available.length)available=pool.filter(team=>team!==other);
    pair[side]=pick(available);
    remember([pair[side]]);
    render();
  }
  function render(){modeName.textContent=LABELS[activeMode]||'Giao hữu';homeTeam.textContent=pair[0]||'---';awayTeam.textContent=pair[1]||'---';}

  root.addEventListener('click',function(e){
    const mode=e.target.closest('[data-friendly-mode]');
    if(mode){activeMode=mode.dataset.friendlyMode;resetHistory();root.querySelectorAll('[data-friendly-mode]').forEach(b=>b.classList.toggle('active',b===mode));drawBoth();return;}
    if(e.target.closest('[data-random-again]')){drawBoth();return;}
    if(e.target.closest('[data-random-home]')){drawOne(0);return;}
    if(e.target.closest('[data-random-away]')){drawOne(1);return;}
  });
  async function loadImportedTierPools(){
    try{
      const response=await fetch('/api/friendly/club-pools',{headers:{'Accept':'application/json'},cache:'no-store'});
      if(!response.ok)return;
      const data=await response.json();
      if(data&&data.ok){
        POOLS.five_star=Array.isArray(data.five_star)?data.five_star:[];
        POOLS.four_star=Array.isArray(data.four_star)?data.four_star:[];
      }
    }catch(_err){}
  }
  loadImportedTierPools().finally(drawBoth);
})();
