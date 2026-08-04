(() => {
    const frame     = document.getElementById('frame');
    const textEl    = document.getElementById('text');
    const emptyNote = document.getElementById('empty-note');
    const hud       = document.getElementById('hud');
    const tally     = document.getElementById('tally');
    const fsBtn     = document.getElementById('fs-btn');
    const clockEl   = document.getElementById('clock');
  
    let hideTimer = null;
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
  
    function render(){
      const { text, style } = SignageStore.getMessage();
  
      frame.classList.toggle('align-left', style.align === 'left');
      textEl.classList.remove('size-sm','size-md','size-lg');
      textEl.classList.add(`size-${style.size}`);
  
      if (!text){
        textEl.classList.remove('in');
        textEl.textContent = '';
        emptyNote.style.display = 'block';
        tally.classList.remove('is-live'); tally.classList.add('is-standby');
        return;
      }
  
      emptyNote.style.display = 'none';
      tally.classList.remove('is-standby'); tally.classList.add('is-live');
  
      if (textEl.textContent === text) return; // no change, skip re-animating
  
      textEl.classList.remove('in');
      // reflow before re-adding the class so the transition replays
      requestAnimationFrame(() => {
        textEl.textContent = text;
        requestAnimationFrame(() => textEl.classList.add('in'));
      });
    }
  
    SignageStore.onMessage((msg) => {
      if (msg && msg.type === 'message-updated') render();
    });
  
    setInterval(render, 4000); // safety-net poll
  
    function tickClock(){
      const now = new Date();
      clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    tickClock();
    setInterval(tickClock, 15000);
  
    fsBtn.addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen().catch(() => {});
    });
  
    render();
  })();