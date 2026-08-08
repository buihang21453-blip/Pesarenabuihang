(function(){
  if (window.__PES_BB_EXT_HOOK__) return; window.__PES_BB_EXT_HOOK__=true;
  const emit=(type,data,level)=>window.postMessage({source:'pes-bb-page',event:{type,level:level||'INFO',ts:new Date().toISOString(),...data}},'*');
  addEventListener('error',e=>emit('js_error',{message:e.message,source:e.filename,line:e.lineno,column:e.colno},'ERROR'),true);
  addEventListener('unhandledrejection',e=>emit('unhandled_rejection',{message:String(e.reason && (e.reason.stack||e.reason.message)||e.reason||'')},'ERROR'));
  if(window.fetch){const f=window.fetch.bind(window);window.fetch=function(input,init){const url=typeof input==='string'?input:(input&&input.url)||'';const method=((init&&init.method)||'GET').toUpperCase();const t=performance.now();return f(input,init).then(r=>{const ms=Math.round(performance.now()-t);emit('fetch',{url:url.slice(0,500),method,status:r.status,duration_ms:ms},(!r.ok?'ERROR':ms>2500?'WARNING':'INFO'));return r}).catch(err=>{emit('fetch_error',{url:url.slice(0,500),method,duration_ms:Math.round(performance.now()-t),message:String(err&&err.message||err)},'ERROR');throw err})}}
  const oldError=console.error.bind(console);console.error=function(){try{emit('console_error',{message:Array.from(arguments).map(x=>typeof x==='string'?x:JSON.stringify(x)).join(' ').slice(0,1000)},'ERROR')}catch(_){}return oldError.apply(console,arguments)};
})();
