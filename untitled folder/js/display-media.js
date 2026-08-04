(() => {
    const stage       = document.getElementById('stage');
    const canvasWrap  = document.getElementById('pdf-canvas-wrap');
    const dotsWrap    = document.getElementById('page-dots');
    const empty       = document.getElementById('empty');
    const hud         = document.getElementById('hud');
    const hudLabel    = document.getElementById('hud-label');
    const tally       = document.getElementById('tally');
    const fsBtn       = document.getElementById('fs-btn');
  
    if (window.pdfjsLib){
      pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
  
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
  
    let currentUrl   = null;   // object URL for <video>
    let currentKind  = null;   // 'pdf' | 'video' | null, tracks what's on screen
    let currentName  = null;   // filename, used to detect "same file, options changed"
    let pdfDoc       = null;
    let pageTimer    = null;
    let pageIndex    = 0;
  
    function clearStage(){
      clearInterval(pageTimer); pageTimer = null;
      canvasWrap.innerHTML = '';
      dotsWrap.innerHTML = '';
      const video = stage.querySelector('video');
      if (video) video.remove();
      if (currentUrl){ URL.revokeObjectURL(currentUrl); currentUrl = null; }
      pdfDoc = null;
    }
  
    async function showVideo(blob, meta){
      clearStage();
      currentUrl = URL.createObjectURL(blob);
      const video = document.createElement('video');
      video.src = currentUrl;
      video.loop = true;
      video.autoplay = true;
      video.muted = meta.muted !== false;
      video.playsInline = true;
      video.controls = false;
      stage.appendChild(video);
      video.play().catch(() => {});
      currentKind = 'video';
      currentName = meta.name;
    }
  
    async function showPdf(blob, meta){
      clearStage();
      const buf = await blob.arrayBuffer();
      pdfDoc = await pdfjsLib.getDocument({ data: buf }).promise;
      currentKind = 'pdf';
      currentName = meta.name;
      pageIndex = 0;
  
      if (pdfDoc.numPages > 1){
        for (let i = 0; i < pdfDoc.numPages; i++){
          const dot = document.createElement('div');
          dot.className = 'dot' + (i === 0 ? ' active' : '');
          dotsWrap.appendChild(dot);
        }
      }
  
      await renderPage(0);
  
      if (pdfDoc.numPages > 1){
        const seconds = Math.max(2, Number(meta.pageSeconds) || 8);
        pageTimer = setInterval(() => {
          pageIndex = (pageIndex + 1) % pdfDoc.numPages;
          renderPage(pageIndex);
        }, seconds * 1000);
      }
    }
  
    async function renderPage(index){
      const page = await pdfDoc.getPage(index + 1);
      const viewportBase = page.getViewport({ scale: 1 });
      const scale = Math.min(
        (window.innerWidth * 0.94) / viewportBase.width,
        (window.innerHeight * 0.9) / viewportBase.height
      );
      const viewport = page.getViewport({ scale });
  
      const canvas = document.createElement('canvas');
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const ctx = canvas.getContext('2d');
      await page.render({ canvasContext: ctx, viewport }).promise;
  
      const prev = canvasWrap.querySelector('canvas');
      canvasWrap.appendChild(canvas);
      requestAnimationFrame(() => canvas.classList.add('in'));
      if (prev) setTimeout(() => prev.remove(), 500);
  
      [...dotsWrap.children].forEach((d, i) => d.classList.toggle('active', i === index));
    }
  
    async function render(){
      const meta = SignageStore.getMediaMeta();
  
      if (!meta){
        clearStage();
        empty.style.display = 'flex';
        hudLabel.textContent = 'CH.01 MEDIA';
        tally.classList.remove('is-live'); tally.classList.add('is-standby');
        currentKind = null; currentName = null;
        return;
      }
  
      empty.style.display = 'none';
      tally.classList.remove('is-standby'); tally.classList.add('is-live');
      hudLabel.textContent = `CH.01 ${meta.type === 'video' ? 'VIDEO' : 'DOCUMENT'}`;
  
      // avoid re-loading/re-flashing when nothing actually changed
      if (currentKind === meta.type && currentName === meta.name) return;
  
      const blob = await SignageStore.getMediaBlob();
      if (!blob) return;
  
      if (meta.type === 'video') await showVideo(blob, meta);
      else await showPdf(blob, meta);
    }
  
    SignageStore.onMessage((msg) => {
      if (!msg) return;
      if (msg.type === 'media-updated' || msg.type === 'ping') render();
    });
  
    // safety-net poll in case a broadcast was missed
    setInterval(() => {
      const meta = SignageStore.getMediaMeta();
      if (!meta && currentKind) render();
      if (meta && !currentKind) render();
    }, 4000);
  
    window.addEventListener('resize', () => {
      if (pdfDoc) renderPage(pageIndex);
    });
  
    fsBtn.addEventListener('click', () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen().catch(() => {});
    });
  
    render();
  })();