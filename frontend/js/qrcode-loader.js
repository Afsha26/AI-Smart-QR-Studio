// Loads QRCode.js from CDN, then imports the ES module `qr.js` and inits it.
(function(){
  'use strict';
  const CDN = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';

  function loadScript(src){
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.async = true;
      s.onload = () => resolve();
      s.onerror = (e) => reject(e);
      document.head.appendChild(s);
    });
  }

  async function boot(){
    try{
      // If QRCode already present, skip CDN
      if(!window.QRCode){
        await loadScript(CDN);
      }
      // Dynamically import ES module
      const mod = await import('./qr.js');
      if(mod && typeof mod.initQR === 'function'){
        mod.initQR();
      }
    }catch(err){
      console.error('Failed to load QRCode or qr.js', err);
    }
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

})();
