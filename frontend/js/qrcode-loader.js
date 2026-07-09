// Loads qr-code-styling from CDN, then imports the ES module `qr.js` and inits it.
(function(){
  'use strict';
  // Using jsDelivr to load a UMD build that exposes `QRCodeStyling` on window
  const CDN = 'https://cdn.jsdelivr.net/npm/qr-code-styling@1.5.0/lib/qr-code-styling.js';

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
      // If QRCodeStyling already present, skip CDN
      if(!window.QRCodeStyling){
        await loadScript(CDN);
      }
      // Dynamically import ES module that uses the global `QRCodeStyling`
      const mod = await import('./qr.js');
      if(mod && typeof mod.initQR === 'function'){
        mod.initQR();
      }
    }catch(err){
      console.error('Failed to load QRCodeStyling or qr.js', err);
    }
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

})();
