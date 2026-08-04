(() => {
    const stage   = document.getElementById('stage');
    const empty   = document.getElementById('empty');
    const hud     = document.getElementById('hud');
    const tally   = document.getElementById('tally');
    const fsBtn   = document.getElementById('fs-btn');
  
    let currentUrl = null;
    let hideTimer  = null;
  
    function wake(){
      hud.classList.remove('faded');
      fsBtn.classList.remove('faded');
      clearTimeout(hideTimer);
      hideTimer = setTimeout(() => {
        hud.classList.add('faded');
        fsBtn.classList.add('faded');
      }, 3500);
    }
    ['mousemove','touchstart','keydown'].forEach(ev => window.addEventListener(ev, wake));
    wake();
  
    async function render(){
      const meta = SignageStore.getPdfMeta();
      const blob = meta ? await SignageStore.getPdfBlob() : null;
  
      if (!blob){
        stage.innerHTML = '';
        empty.style.display = 'flex';
        tally.classList.remove('is-live'); tally.classList.add('is-standby');
        if (currentUrl){ URL.revokeObjectURL(currentUrl); currentUrl = null; }
        return;
      }
  
      empty.style.display = 'none';
      tally.classList.remove('is-standby'); tally.classList.add('is-live');
  
      if (currentUrl) URL.revokeObjectURL(currentUrl);
      currentUrl = URL.createObjectURL(blob);
      stage.innerHTML = `<iframe src="${currentUrl}#toolbar=0&navpanes=0&view=FitH" title="Document"></iframe>`;
    }
  
    SignageStore.onMessage((msg) => {
      if (msg && msg.type === 'pdf-updated') render();
    });
  
    // in case this tab was opened before the file finished writing, or storage
    // event support is flaky across browsers, poll softly as a safety net
    setInterval(() => {
      const meta = SignageStore.getPdfMeta();
      const has = !!stage.querySelector('iframe');
      if ((meta && !has) || (!meta && has)) render();
    }, 4000);
  
    fsBtn.addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen().catch(() => {});
    });
  
    render();
  })();