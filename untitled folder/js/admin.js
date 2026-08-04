(() => {
    const dropzone     = document.getElementById('dropzone');
    const pdfInput      = document.getElementById('pdf-input');
    const fileRow       = document.getElementById('file-row');
    const fileName      = document.getElementById('file-name');
    const fileSub       = document.getElementById('file-sub');
    const previewFrame  = document.getElementById('preview-frame');
    const clearPdfBtn   = document.getElementById('clear-pdf');
    const tallyPdf      = document.getElementById('tally-pdf');
  
    const msgInput      = document.getElementById('msg-input');
    const msgPreview    = document.getElementById('msg-preview');
    const msgPreviewText= document.getElementById('msg-preview-text');
    const msgTimestamp  = document.getElementById('msg-timestamp');
    const publishBtn    = document.getElementById('publish-msg');
    const clearMsgBtn   = document.getElementById('clear-msg');
    const segSize       = document.getElementById('seg-size');
    const segAlign      = document.getElementById('seg-align');
    const tallyMsg      = document.getElementById('tally-msg');
  
    const toast = document.getElementById('toast');
    let toastTimer = null;
    function showToast(text){
      toast.textContent = text;
      toast.classList.add('show');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
    }
  
    function fmtBytes(n){
      if (!n && n !== 0) return '—';
      const u = ['B','KB','MB','GB']; let i = 0;
      while (n >= 1024 && i < u.length - 1){ n /= 1024; i++; }
      return `${n.toFixed(i === 0 ? 0 : 1)} ${u[i]}`;
    }
    function fmtTime(ts){
      if (!ts) return 'Not published yet';
      const d = new Date(ts);
      return `Updated ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
  
    // ---------------- OUTPUT 1: DOCUMENT ----------------
  
    let currentPdfUrl = null;
  
    async function refreshPdfUI(){
      const meta = SignageStore.getPdfMeta();
      if (!meta){
        fileRow.classList.add('empty');
        fileName.textContent = 'No document loaded';
        fileSub.textContent = '—';
        previewFrame.innerHTML = '<div class="preview-empty">Preview appears once a PDF is loaded</div>';
        tallyPdf.classList.remove('is-live'); tallyPdf.classList.add('is-standby');
        if (currentPdfUrl){ URL.revokeObjectURL(currentPdfUrl); currentPdfUrl = null; }
        return;
      }
      fileRow.classList.remove('empty');
      fileName.textContent = meta.name;
      fileSub.textContent = `${fmtBytes(meta.size)} · ${fmtTime(meta.updatedAt)}`;
      tallyPdf.classList.remove('is-standby'); tallyPdf.classList.add('is-live');
  
      const blob = await SignageStore.getPdfBlob();
      if (blob){
        if (currentPdfUrl) URL.revokeObjectURL(currentPdfUrl);
        currentPdfUrl = URL.createObjectURL(blob);
        previewFrame.innerHTML = `<iframe src="${currentPdfUrl}#toolbar=0&view=FitH" title="Document preview"></iframe>`;
      }
    }
  
    async function handleFile(file){
      if (!file) return;
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')){
        showToast('Please choose a PDF file');
        return;
      }
      await SignageStore.setPdf(file);
      await refreshPdfUI();
      showToast('Document sent to Output 1');
    }
  
    pdfInput.addEventListener('change', (e) => handleFile(e.target.files[0]));
  
    ['dragenter','dragover'].forEach(ev => dropzone.addEventListener(ev, (e) => {
      e.preventDefault(); dropzone.classList.add('drag');
    }));
    ['dragleave','drop'].forEach(ev => dropzone.addEventListener(ev, (e) => {
      e.preventDefault(); dropzone.classList.remove('drag');
    }));
    dropzone.addEventListener('drop', (e) => {
      const file = e.dataTransfer.files && e.dataTransfer.files[0];
      handleFile(file);
    });
  
    clearPdfBtn.addEventListener('click', async () => {
      await SignageStore.clearPdf();
      await refreshPdfUI();
      showToast('Output 1 cleared');
    });
  
    // ---------------- OUTPUT 2: MESSAGE ----------------
  
    function applyStyleToPreview(style){
      msgPreview.className = `msg-preview size-${style.size} align-${style.align}`;
      segSize.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.size === style.size));
      segAlign.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.align === style.align));
    }
  
    function refreshMessageUI(){
      const { text, style, updatedAt } = SignageStore.getMessage();
      if (document.activeElement !== msgInput) msgInput.value = text;
      msgPreviewText.textContent = text;
      applyStyleToPreview(style);
      msgTimestamp.textContent = fmtTime(updatedAt);
      tallyMsg.classList.toggle('is-live', !!text);
      tallyMsg.classList.toggle('is-standby', !text);
    }
  
    let liveStyle = SignageStore.getMessageStyle();
  
    segSize.addEventListener('click', (e) => {
      const btn = e.target.closest('button'); if (!btn) return;
      liveStyle = { ...liveStyle, size: btn.dataset.size };
      applyStyleToPreview(liveStyle);
      SignageStore.setMessageStyle(liveStyle);
    });
    segAlign.addEventListener('click', (e) => {
      const btn = e.target.closest('button'); if (!btn) return;
      liveStyle = { ...liveStyle, align: btn.dataset.align };
      applyStyleToPreview(liveStyle);
      SignageStore.setMessageStyle(liveStyle);
    });
  
    msgInput.addEventListener('input', () => {
      msgPreviewText.textContent = msgInput.value;
    });
  
    publishBtn.addEventListener('click', () => {
      SignageStore.setMessage(msgInput.value, liveStyle);
      refreshMessageUI();
      showToast('Message published to Output 2');
    });
  
    clearMsgBtn.addEventListener('click', () => {
      SignageStore.clearMessage();
      msgInput.value = '';
      refreshMessageUI();
      showToast('Output 2 cleared');
    });
  
    // publish on Cmd/Ctrl+Enter as a shortcut
    msgInput.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter'){
        publishBtn.click();
      }
    });
  
    // ---------------- cross-tab sync ----------------
  
    SignageStore.onMessage((msg) => {
      if (!msg) return;
      if (msg.type === 'pdf-updated') refreshPdfUI();
      if (msg.type === 'message-updated') refreshMessageUI();
    });
  
    // ---------------- init ----------------
    refreshPdfUI();
    refreshMessageUI();
  })();