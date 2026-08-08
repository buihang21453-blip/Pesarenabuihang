(function(){
  if(window.__PES_BB_EXT_CONTENT__) return; window.__PES_BB_EXT_CONTENT__=true;
  const script=document.createElement('script');script.src=chrome.runtime.getURL('page-hook.js');script.onload=()=>script.remove();(document.head||document.documentElement).appendChild(script);
  const events=[]; const MAX=500; const cutoff=()=>Date.now()-60000;
  function scrub(v){if(v==null)return v;if(typeof v==='string')return v.slice(0,1200);if(Array.isArray(v))return v.slice(0,30).map(scrub);if(typeof v==='object'){const o={};Object.keys(v).slice(0,50).forEach(k=>o[k]=/password|secret|token|authorization|cookie|session|parsec/i.test(k)?'[redacted]':scrub(v[k]));return o}return v}
  function add(e){events.push(scrub(e));while(events.length>MAX||events.length&&Date.parse(events[0].ts)<cutoff())events.shift()}
  add({type:'extension_start',level:'INFO',ts:new Date().toISOString(),url:location.href});
  addEventListener('message',e=>{if(e.source===window&&e.data&&e.data.source==='pes-bb-page')add(e.data.event)});
  document.addEventListener('click',e=>{const el=e.target.closest&&e.target.closest('button,a,[role="button"],input[type="submit"]');if(!el)return;add({type:'ui_click',level:'INFO',ts:new Date().toISOString(),tag:el.tagName,id:el.id||null,text:(el.innerText||el.value||'').trim().slice(0,120)})},true);
  chrome.runtime.onMessage.addListener((msg,sender,sendResponse)=>{
    if(msg&&msg.type==='GET_REPORT'){
      const report={generated_at:new Date().toISOString(),url:location.href,title:document.title,user_agent:navigator.userAgent,viewport:{width:innerWidth,height:innerHeight},online:navigator.onLine,visibility:document.visibilityState,events:events.slice(),dom:{body_class:document.body&&document.body.className||'',page:document.body&&document.body.dataset&&document.body.dataset.page||'',active_element:document.activeElement&&document.activeElement.tagName||null}};
      sendResponse(report);return true;
    }
    if(msg&&msg.type==='GET_STATUS'){sendResponse({events:events.length,errors:events.filter(x=>x.level==='ERROR').length,warnings:events.filter(x=>x.level==='WARNING').length,url:location.href});return true}
  });
})();
