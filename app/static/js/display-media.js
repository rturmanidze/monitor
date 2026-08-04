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
      window.location.reload();
    }
  });

  socket.addEventListener('close', () => {
    window.clearInterval(heartbeat);
    window.setTimeout(connectMediaSocket, 2000);
  });
}

connectMediaSocket();
