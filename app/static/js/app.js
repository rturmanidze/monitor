document.querySelectorAll('.js-post').forEach((button) => {
  button.addEventListener('click', async () => {
    await fetch(button.dataset.url, { method: 'POST' });
    window.location.reload();
  });
});

document.querySelectorAll('.js-delete').forEach((button) => {
  button.addEventListener('click', async () => {
    if (!window.confirm('Delete this item?')) return;
    await fetch(button.dataset.url, { method: 'DELETE' });
    window.location.reload();
  });
});

document.querySelectorAll('[data-uptime]').forEach((node) => {
  const seconds = Number(node.dataset.uptime || '0');
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  node.textContent = `${hours}h ${minutes}m`;
});
