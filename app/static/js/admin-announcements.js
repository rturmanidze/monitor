// Admin Announcements Page JS

// ── Quill setup ──────────────────────────────────────────────────────────────
const quill = new Quill('#quill-editor', {
  theme: 'snow',
  placeholder: 'Type your announcement message…',
  modules: {
    toolbar: [
      [{ size: ['small', false, 'large', 'huge'] }],
      ['bold', 'italic', 'underline'],
      [{ color: [] }, { background: [] }],
      [{ align: [] }],
      [{ list: 'ordered' }, { list: 'bullet' }],
      ['clean'],
    ],
    history: { delay: 500, maxStack: 100, userOnly: true },
  },
});

// ── State ─────────────────────────────────────────────────────────────────────
let editingId = null;   // null = create mode, number = edit mode

const titleInput      = document.getElementById('ann-title');
const durationInput   = document.getElementById('ann-duration');
const alignSelect     = document.getElementById('ann-alignment');
const animSelect      = document.getElementById('ann-animation');
const bgColorInput    = document.getElementById('ann-bg-color');
const enabledCheck    = document.getElementById('ann-enabled');
const pinnedCheck     = document.getElementById('ann-pinned');
const saveBtn         = document.getElementById('save-announcement-btn');
const cancelBtn       = document.getElementById('cancel-edit-btn');
const submitForm      = document.getElementById('announcement-submit-form');

// ── Live preview via WebSocket ────────────────────────────────────────────────
function refreshPreview() {
  const iframe = document.getElementById('live-preview-iframe');
  if (iframe) {
    iframe.src = iframe.src;
  }
}

let previewDebounce = null;
function schedulePreview() {
  clearTimeout(previewDebounce);
  previewDebounce = setTimeout(refreshPreview, 800);
}

// Refresh preview when quill content changes (live typing)
quill.on('text-change', schedulePreview);
titleInput.addEventListener('input', schedulePreview);
bgColorInput.addEventListener('input', schedulePreview);
alignSelect.addEventListener('change', schedulePreview);

// ── WebSocket for live display sync ──────────────────────────────────────────
function connectLiveSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/live`);
  let heartbeat;

  socket.addEventListener('open', () => {
    heartbeat = window.setInterval(() => socket.send('ping'), 15000);
  });

  socket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    if (data.event === 'announcements-updated') {
      refreshPreview();
    }
  });

  socket.addEventListener('close', () => {
    window.clearInterval(heartbeat);
    window.setTimeout(connectLiveSocket, 2000);
  });
}

// ── Form submission ───────────────────────────────────────────────────────────
function populateAndSubmit() {
  const htmlContent = quill.getSemanticHTML();

  submitForm.elements['title'].value           = titleInput.value;
  submitForm.elements['message'].value         = htmlContent;
  submitForm.elements['duration_seconds'].value = durationInput.value;
  submitForm.elements['background_color'].value = bgColorInput.value;
  submitForm.elements['alignment'].value       = alignSelect.value;
  submitForm.elements['animation'].value       = animSelect.value;
  submitForm.elements['enabled'].value         = enabledCheck.checked ? 'true' : 'false';
  submitForm.elements['pinned'].value          = pinnedCheck.checked ? 'true' : 'false';

  if (editingId !== null) {
    submitForm.action = `/api/announcements/${editingId}/update`;
    submitForm.elements['archived'].value = 'false';
  } else {
    submitForm.action = '/api/announcements';
  }

  submitForm.submit();
}

saveBtn.addEventListener('click', () => {
  if (!titleInput.value.trim()) {
    titleInput.focus();
    return;
  }
  populateAndSubmit();
});

// ── Cancel edit ───────────────────────────────────────────────────────────────
cancelBtn.addEventListener('click', () => {
  editingId = null;
  titleInput.value = '';
  quill.setContents([]);
  durationInput.value = 10;
  bgColorInput.value = '#111827';
  alignSelect.value = 'center';
  animSelect.value = 'fade';
  enabledCheck.checked = true;
  pinnedCheck.checked = false;
  saveBtn.textContent = 'Save Announcement';
  cancelBtn.style.display = 'none';
});

// ── Edit buttons ──────────────────────────────────────────────────────────────
document.querySelectorAll('.js-edit-announcement').forEach((btn) => {
  btn.addEventListener('click', () => {
    const data = JSON.parse(btn.closest('[data-announcement]').dataset.announcement);
    editingId = data.id;

    titleInput.value    = data.title || '';
    durationInput.value = data.duration_seconds || 10;
    bgColorInput.value  = data.background_color || '#111827';
    alignSelect.value   = data.alignment || 'center';
    animSelect.value    = data.animation || 'fade';
    enabledCheck.checked = Boolean(data.enabled);
    pinnedCheck.checked  = Boolean(data.pinned);

    // Load HTML message into Quill
    quill.clipboard.dangerouslyPasteHTML(data.message || '');

    saveBtn.textContent = 'Update Announcement';
    cancelBtn.style.display = '';
    document.getElementById('editor-card').scrollIntoView({ behavior: 'smooth' });
  });
});

// ── Drag-to-reorder ───────────────────────────────────────────────────────────
const list = document.getElementById('announcement-list');
if (list) {
  let dragged = null;
  list.querySelectorAll('[data-announcement-id]').forEach((item) => {
    item.addEventListener('dragstart', () => {
      dragged = item;
      item.classList.add('dragging');
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      const payload = Array.from(list.querySelectorAll('[data-announcement-id]')).map((node) => ({ id: node.dataset.announcementId }));
      fetch(`/api/announcements/reorder?payload=${encodeURIComponent(JSON.stringify(payload))}`, { method: 'POST' });
    });
    item.addEventListener('dragover', (event) => {
      event.preventDefault();
      const target = event.currentTarget;
      if (dragged && dragged !== target) {
        const rect = target.getBoundingClientRect();
        const next = (event.clientY - rect.top) / rect.height > 0.5;
        list.insertBefore(dragged, next ? target.nextSibling : target);
      }
    });
  });
}

connectLiveSocket();
