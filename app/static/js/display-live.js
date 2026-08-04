const appNode = document.getElementById('liveAnnouncementApp');
let announcements = [];
let currentIndex = 0;
let timer = null;

function normalize(items) {
  return (items || []).filter((item) => item.enabled && !item.archived).sort((a, b) => Number(b.pinned) - Number(a.pinned) || a.sort_order - b.sort_order || b.priority - a.priority);
}

function renderAnnouncement(item) {
  if (!item) {
    appNode.innerHTML = '<div class="empty-display">No live announcements available.</div>';
    return;
  }
  appNode.innerHTML = `
    <div class="announcement-stage text-${item.alignment} ${item.font_size}" style="color:${item.text_color};background:${item.background_color};">
      <div class="announcement-inner ${item.bold ? 'fw-bold' : ''} ${item.italic ? 'fst-italic' : ''} ${item.underline ? 'text-decoration-underline' : ''}">
        <div class="announcement-title">${item.title}</div>
        <div class="announcement-message">${item.message}</div>
      </div>
    </div>`;
}

function cycleAnnouncements() {
  window.clearTimeout(timer);
  if (!announcements.length) {
    renderAnnouncement(null);
    return;
  }
  const item = announcements[currentIndex % announcements.length];
  renderAnnouncement(item);
  currentIndex = (currentIndex + 1) % announcements.length;
  timer = window.setTimeout(cycleAnnouncements, (item.duration_seconds || 10) * 1000);
}

async function refreshAnnouncements() {
  const response = await fetch('/api/history');
  if (!response.ok) return;
}

function connectLiveSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/live`);
  let heartbeat;

  socket.addEventListener('open', () => {
    heartbeat = window.setInterval(() => socket.send('ping'), 15000);
  });

  socket.addEventListener('message', async (event) => {
    const data = JSON.parse(event.data);
    if (data.event === 'announcements-updated') {
      const response = await fetch('/api/announcements/feed');
      if (response.ok) {
        announcements = normalize(await response.json());
        currentIndex = 0;
        cycleAnnouncements();
      } else {
        window.location.reload();
      }
    }
  });

  socket.addEventListener('close', () => {
    window.clearInterval(heartbeat);
    window.setTimeout(connectLiveSocket, 2000);
  });
}

try {
  announcements = normalize(JSON.parse(appNode.dataset.announcements || '[]'));
} catch {
  announcements = [];
}
cycleAnnouncements();
connectLiveSocket();
