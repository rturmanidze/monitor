/* =========================================================
   SIGNAGE CONSOLE — shared store
   One origin, two outputs:
     CH.01  MEDIA     -> a PDF or a video, kept in IndexedDB, always loops
     CH.02  MESSAGE   -> free text, kept in localStorage (tiny, instant)
   BroadcastChannel pushes changes to every open tab immediately;
   IndexedDB/localStorage is the source of truth on load/refresh.
   ========================================================= */

   const SignageStore = (() => {

    const DB_NAME    = 'signage-console';
    const DB_VERSION = 1;
    const STORE_NAME = 'files';
    const CHANNEL    = 'signage-console-bus';
  
    const LS_TEXT_KEY   = 'signage.message.text';
    const LS_STYLE_KEY  = 'signage.message.style';
    const LS_TEXT_META  = 'signage.message.updatedAt';
    const LS_MEDIA_META = 'signage.media.meta'; // { name, size, type: 'pdf'|'video', updatedAt, pageSeconds, muted }
  
    let bus = null;
    try { bus = new BroadcastChannel(CHANNEL); } catch (e) { bus = null; }
  
    function openDB(){
      return new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = () => {
          const db = req.result;
          if (!db.objectStoreNames.contains(STORE_NAME)){
            db.createObjectStore(STORE_NAME);
          }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror   = () => reject(req.error);
      });
    }
  
    async function idbPut(key, value){
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).put(value, key);
        tx.oncomplete = () => resolve(true);
        tx.onerror    = () => reject(tx.error);
      });
    }
  
    async function idbGet(key){
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const req = tx.objectStore(STORE_NAME).get(key);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror   = () => reject(req.error);
      });
    }
  
    async function idbDelete(key){
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).delete(key);
        tx.oncomplete = () => resolve(true);
        tx.onerror    = () => reject(tx.error);
      });
    }
  
    function notify(type, payload){
      if (bus) bus.postMessage({ type, payload, ts: Date.now() });
      // also touch a localStorage key so the native 'storage' event fires in
      // other tabs as a fallback path when BroadcastChannel isn't available
      try { localStorage.setItem('signage.ping', String(Date.now())); } catch (e) {}
    }
  
    function onMessage(handler){
      const fns = [];
      if (bus){
        const fn = (ev) => handler(ev.data);
        bus.addEventListener('message', fn);
        fns.push(() => bus.removeEventListener('message', fn));
      }
      const storageFn = (ev) => {
        if (ev.key === 'signage.ping') handler({ type: 'ping' });
      };
      window.addEventListener('storage', storageFn);
      fns.push(() => window.removeEventListener('storage', storageFn));
      return () => fns.forEach(f => f());
    }
  
    function detectType(file){
      if (file.type === 'application/pdf' || /\.pdf$/i.test(file.name)) return 'pdf';
      if (file.type.startsWith('video/') || /\.(mp4|webm|mov|m4v|ogg)$/i.test(file.name)) return 'video';
      return null;
    }
  
    // ---------------- MEDIA (CH.01 — pdf or video, always loops) ----------------
  
    async function setMedia(file){
      const type = detectType(file);
      if (!type) throw new Error('Unsupported file type. Use a PDF or a video (mp4/webm/mov).');
      const buf = await file.arrayBuffer();
      const mime = type === 'pdf' ? 'application/pdf' : (file.type || 'video/mp4');
      await idbPut('media-blob', new Blob([buf], { type: mime }));
      const prev = getMediaMeta() || {};
      const meta = {
        name: file.name,
        size: file.size,
        type,
        updatedAt: Date.now(),
        pageSeconds: prev.pageSeconds || 8,
        muted: prev.muted !== undefined ? prev.muted : true
      };
      localStorage.setItem(LS_MEDIA_META, JSON.stringify(meta));
      notify('media-updated', meta);
      return meta;
    }
  
    async function getMediaBlob(){
      return idbGet('media-blob');
    }
  
    function getMediaMeta(){
      try { return JSON.parse(localStorage.getItem(LS_MEDIA_META)) || null; }
      catch (e) { return null; }
    }
  
    function setMediaOptions(partial){
      const meta = getMediaMeta();
      if (!meta) return null;
      const next = { ...meta, ...partial };
      localStorage.setItem(LS_MEDIA_META, JSON.stringify(next));
      notify('media-updated', next);
      return next;
    }
  
    async function clearMedia(){
      await idbDelete('media-blob');
      localStorage.removeItem(LS_MEDIA_META);
      notify('media-updated', null);
    }
  
    // ---------------- MESSAGE (CH.02) ----------------
  
    function setMessage(text, style){
      localStorage.setItem(LS_TEXT_KEY, text);
      localStorage.setItem(LS_TEXT_META, String(Date.now()));
      if (style) localStorage.setItem(LS_STYLE_KEY, JSON.stringify(style));
      const payload = { text, style: getMessageStyle(), updatedAt: Date.now() };
      notify('message-updated', payload);
      return payload;
    }
  
    function getMessage(){
      return {
        text: localStorage.getItem(LS_TEXT_KEY) || '',
        style: getMessageStyle(),
        updatedAt: Number(localStorage.getItem(LS_TEXT_META) || 0)
      };
    }
  
    function getMessageStyle(){
      try { return JSON.parse(localStorage.getItem(LS_STYLE_KEY)) || defaultStyle(); }
      catch (e) { return defaultStyle(); }
    }
  
    function setMessageStyle(style){
      localStorage.setItem(LS_STYLE_KEY, JSON.stringify(style));
      notify('message-updated', getMessage());
    }
  
    function defaultStyle(){
      return { size: 'lg', align: 'center', theme: 'dark' };
    }
  
    function clearMessage(){
      localStorage.removeItem(LS_TEXT_KEY);
      localStorage.removeItem(LS_TEXT_META);
      notify('message-updated', { text: '', style: getMessageStyle(), updatedAt: Date.now() });
    }
  
    return {
      onMessage,
      setMedia, getMediaBlob, getMediaMeta, setMediaOptions, clearMedia,
      setMessage, getMessage, setMessageStyle, getMessageStyle, clearMessage
    };
  })();