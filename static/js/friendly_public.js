(function () {
  'use strict';

  // Static client-side pools: no API, Supabase, Realtime or Storage request is
  // performed when selecting a mode or pressing Random again.
  const POOLS = {
    premier_league: [
      'Arsenal','Aston Villa','Bournemouth','Brentford','Brighton','Burnley',
      'Chelsea','Crystal Palace','Everton','Fulham','Leeds United','Liverpool',
      'Manchester City','Manchester United','Newcastle United','Nottingham Forest',
      'Sunderland','Tottenham Hotspur','West Ham United','Wolverhampton'
    ],
    la_liga: [
      'Athletic Club','Atlético Madrid','Barcelona','Celta Vigo','Elche','Espanyol',
      'Getafe','Girona','Levante','Mallorca','Osasuna','Rayo Vallecano','Real Betis',
      'Real Madrid','Real Oviedo','Real Sociedad','Sevilla','Valencia','Villarreal','Alavés'
    ],
    five_star: [
      'Manchester City','Real Madrid','Bayern Munich','Inter Milan',
      'Arsenal','Liverpool','Barcelona','PSG'
    ],
    four_star: [
      'Atlético Madrid','Bayer Leverkusen','Borussia Dortmund',
      'Tottenham Hotspur','AC Milan','Juventus'
    ],
    club_five_star: [
      'Real Madrid','Barcelona','Liverpool','Arsenal','Manchester City',
      'Paris Saint-Germain','Inter Milan','Bayern Munich'
    ],
    nation_five_star: [
      'Tây Ban Nha','Pháp','Brazil','Anh','Argentina','Bồ Đào Nha','Đức','Hà Lan'
    ]
  };

  const LABELS = {
    premier_league: 'Ngoại Hạng Anh',
    la_liga: 'La Liga',
    five_star: '5 Sao',
    four_star: '4 Sao',
    club_five_star: 'CLB 5★',
    nation_five_star: 'Quốc Gia 5★'
  };

  const root = document.querySelector('[data-friendly-randomizer]');
  if (!root) return;

  const home = root.querySelector('[data-friendly-home]');
  const result = root.querySelector('[data-friendly-result]');
  const homeTeam = root.querySelector('[data-home-team]');
  const awayTeam = root.querySelector('[data-away-team]');
  const modeName = root.querySelector('[data-mode-name]');
  let activeMode = '';

  function randomIndex(max) {
    if (window.crypto && window.crypto.getRandomValues) {
      const values = new Uint32Array(1);
      window.crypto.getRandomValues(values);
      return values[0] % max;
    }
    return Math.floor(Math.random() * max);
  }

  function pickPair(pool) {
    const firstIndex = randomIndex(pool.length);
    let secondIndex = randomIndex(pool.length - 1);
    if (secondIndex >= firstIndex) secondIndex += 1;
    return [pool[firstIndex], pool[secondIndex]];
  }

  function draw(mode) {
    const pool = POOLS[mode] || [];
    if (pool.length < 2) return;
    activeMode = mode;
    const pair = pickPair(pool);
    modeName.textContent = LABELS[mode] || 'Giao hữu';
    homeTeam.textContent = pair[0];
    awayTeam.textContent = pair[1];
    home.hidden = true;
    result.hidden = false;
  }

  root.addEventListener('click', function (event) {
    const modeButton = event.target.closest('[data-friendly-mode]');
    if (modeButton) {
      draw(modeButton.dataset.friendlyMode);
      return;
    }
    if (event.target.closest('[data-random-again]') && activeMode) {
      draw(activeMode);
      return;
    }
    if (event.target.closest('[data-friendly-back]')) {
      result.hidden = true;
      home.hidden = false;
    }
  });
})();
