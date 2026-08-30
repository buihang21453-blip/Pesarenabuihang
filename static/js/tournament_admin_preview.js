(function(){
  const root=document.getElementById('tournament-design-admin');
  if(!root)return;
  const form=document.getElementById('tournament-design-form');
  const cup=document.getElementById('preview-hero-cup');
  const badge=document.getElementById('preview-arena-badge');
  const controls={};
  form.querySelectorAll('[data-preview-control]').forEach(input=>{controls[input.name]=input;});
  const defaults={hero_cup_width:220,hero_cup_right:24,hero_cup_bottom:-14,arena_badge_width:230,arena_badge_x:50,arena_badge_y:46};
  function value(name){return Number(controls[name]&&controls[name].value)||0;}
  function update(){
    form.querySelectorAll('output[data-output-for]').forEach(out=>{const n=out.dataset.outputFor;out.value=String(value(n))+(n.includes('_x')||n.includes('_y')?'%':' px');});
    // Preview is scaled down from the real page so position values stay visually representative.
    const cupScale=.62;
    cup.style.width=(value('hero_cup_width')*cupScale)+'px';
    cup.style.right=(value('hero_cup_right')*cupScale)+'px';
    cup.style.bottom=(value('hero_cup_bottom')*cupScale)+'px';
    const badgeScale=.62;
    badge.style.width=(value('arena_badge_width')*badgeScale)+'px';
    badge.style.left=value('arena_badge_x')+'%';
    badge.style.top=value('arena_badge_y')+'%';
  }
  Object.values(controls).forEach(input=>input.addEventListener('input',update));
  const reset=document.getElementById('tournament-design-reset-preview');
  if(reset)reset.addEventListener('click',()=>{Object.entries(defaults).forEach(([k,v])=>{if(controls[k])controls[k].value=v;});update();});
  update();
})();
