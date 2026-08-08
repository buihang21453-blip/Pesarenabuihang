chrome.runtime.onMessage.addListener((msg,sender,sendResponse)=>{
  if(msg&&msg.type==='CAPTURE_VISIBLE'){
    chrome.tabs.captureVisibleTab(null,{format:'png'},dataUrl=>{sendResponse({ok:!chrome.runtime.lastError,dataUrl,error:chrome.runtime.lastError&&chrome.runtime.lastError.message});});return true;
  }
  if(msg&&msg.type==='DOWNLOAD_REPORT'){
    const blobText=JSON.stringify(msg.report,null,2);const url='data:application/json;charset=utf-8,'+encodeURIComponent(blobText);chrome.downloads.download({url,filename:'PES_Arena_BlackBox_'+Date.now()+'.json',saveAs:true});sendResponse({ok:true});return true;
  }
});
