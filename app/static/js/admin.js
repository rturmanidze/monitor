const editModalElement = document.getElementById('editAnnouncementModal');
const editForm = document.getElementById('edit-announcement-form');
const templateButtons = document.querySelectorAll('.js-template-apply');
const createForm = document.getElementById('announcement-form');

if (editModalElement && editForm) {
  const modal = new bootstrap.Modal(editModalElement);
  document.querySelectorAll('.js-edit-announcement').forEach((button) => {
    button.addEventListener('click', () => {
      const data = JSON.parse(button.dataset.announcement);
      editForm.action = `/api/announcements/${data.id}/update`;
      Array.from(editForm.elements).forEach((field) => {
        if (!field.name) return;
        if (field.type === 'checkbox') {
          field.checked = Boolean(data[field.name]);
        } else if (field.name in data) {
          field.value = data[field.name];
        }
      });
      modal.show();
    });
  });
}

templateButtons.forEach((button) => {
  button.addEventListener('click', async () => {
    const response = await fetch(`/api/templates/${button.dataset.templateId}/apply`, { method: 'POST' });
    const data = await response.json();
    Object.entries(data).forEach(([key, value]) => {
      const field = createForm.elements.namedItem(key);
      if (!field) return;
      if (field.type === 'checkbox') {
        field.checked = Boolean(value);
      } else {
        field.value = value;
      }
    });
    window.scrollTo({ top: createForm.offsetTop - 50, behavior: 'smooth' });
  });
});

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
