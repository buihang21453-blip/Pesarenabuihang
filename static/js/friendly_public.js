(function () {
  'use strict';
  const POOLS = {
    premier_league:['Arsenal','Aston Villa','Bournemouth','Brentford','Brighton','Burnley','Chelsea','Crystal Palace','Everton','Fulham','Leeds United','Liverpool','Manchester City','Manchester United','Newcastle United','Nottingham Forest','Sunderland','Tottenham Hotspur','West Ham United','Wolverhampton'],
    la_liga:['Athletic Club','Atlético Madrid','Barcelona','Celta Vigo','Elche','Espanyol','Getafe','Girona','Levante','Mallorca','Osasuna','Rayo Vallecano','Real Betis','Real Madrid','Real Oviedo','Real Sociedad','Sevilla','Valencia','Villarreal','Alavés'],
    five_star:['Manchester City','Real Madrid','Bayern Munich','Inter Milan','Arsenal','Liverpool','Barcelona','PSG'],
    four_star:['Atlético Madrid','Bayer Leverkusen','Borussia Dortmund','Tottenham Hotspur','AC Milan','Juventus'],
    club_five_star:['Real Madrid','Barcelona','Liverpool','Arsenal','Manchester City','Paris Saint-Germain','Inter Milan','Bayern Munich'],
    nation_five_star:['Tây Ban Nha','Pháp','Brazil','Anh','Argentina','Bồ Đào Nha','Đức','Hà Lan']
  };
  const LABELS={premier_league:'Ngoại Hạng Anh',la_liga:'La Liga',five_star:'5 Sao',four_star:'4 Sao',club_five_star:'CLB 5★',nation_five_star:'Quốc Gia 5★'};
  const root=document.querySelector('[data-friendly-randomizer]'); if(!root)return;
  const homeTeam=root.querySelector('[data-home-team]'),awayTeam=root.querySelector('[data-away-team]'),modeName=root.querySelector('[data-mode-name]');
  let activeMode='premier_league', pair=['',''];
  function randomIndex(max){if(window.crypto&&window.crypto.getRandomValues){const v=new Uint32Array(1);window.crypto.getRandomValues(v);return v[0]%max;}return Math.floor(Math.random()*max);}
  function different(pool,other){if(pool.length<2)return pool[0]||'---';let value=pool[randomIndex(pool.length)];while(value===other)value=pool[randomIndex(pool.length)];return value;}
  function drawBoth(){const pool=POOLS[activeMode];pair[0]=pool[randomIndex(pool.length)];pair[1]=different(pool,pair[0]);render();}
  function render(){modeName.textContent=LABELS[activeMode]||'Giao hữu';homeTeam.textContent=pair[0]||'---';awayTeam.textContent=pair[1]||'---';}
  root.addEventListener('click',function(e){const mode=e.target.closest('[data-friendly-mode]');if(mode){activeMode=mode.dataset.friendlyMode;root.querySelectorAll('[data-friendly-mode]').forEach(b=>b.classList.toggle('active',b===mode));drawBoth();return;}if(e.target.closest('[data-random-again]')){drawBoth();return;}if(e.target.closest('[data-random-home]')){pair[0]=different(POOLS[activeMode],pair[1]);render();return;}if(e.target.closest('[data-random-away]')){pair[1]=different(POOLS[activeMode],pair[0]);render();}});
  drawBoth();
})();
