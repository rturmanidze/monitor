// Admin Media Page JS

function connectMediaSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/media`);
  let heartbeat;

  socket.addEventListener('open', () => {
    heartbeat = window.setInterval(() => socket.send('ping'), 15000);
  });

  socket.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    if (data.event === 'media-updated') {
      // Reload the preview iframe
      const iframe = document.getElementById('media-preview-iframe');
      if (iframe) {
        iframe.src = iframe.src;
      }
      // Reload the page to refresh the file list and info
      window.location.reload();
    }
  });

  socket.addEventListener('close', () => {
    window.clearInterval(heartbeat);
    window.setTimeout(connectMediaSocket, 2000);
  });
}

// js-post: submit a POST form fetch, then reload
document.querySelectorAll('.js-post').forEach((btn) => {
  btn.addEventListener('click', async () => {
    await fetch(btn.dataset.url, { method: 'POST' });
    window.location.reload();
  });
});

// js-delete: send DELETE fetch, then reload
document.querySelectorAll('.js-delete').forEach((btn) => {
  btn.addEventListener('click', async () => {
    if (!window.confirm('Delete this media item?')) return;
    await fetch(btn.dataset.url, { method: 'DELETE' });
    window.location.reload();
  });
});

connectMediaSocket();
