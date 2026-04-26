/* ── Image preview ─────────────────────────────────────────────────────── */
(function () {
  const input = document.getElementById('img-input');
  const preview = document.getElementById('img-preview');
  const previewWrap = document.getElementById('img-preview-wrap');
  const label = document.getElementById('img-input-label');
  const labelText = document.getElementById('img-input-label-text');

  if (!input) return;

  input.addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
      if (preview) { preview.src = e.target.result; }
      if (previewWrap) { previewWrap.style.display = 'block'; }
      if (label) { label.classList.add('has-file'); }
      if (labelText) { labelText.textContent = file.name; }
    };
    reader.readAsDataURL(file);
  });
})();

/* ── Voting card toggling ──────────────────────────────────────────────── */
(function () {
  const grid = document.getElementById('vote-grid');
  if (!grid) return;

  const categoryId = grid.dataset.category;
  const votesPerCategory = parseInt(grid.dataset.votesPerCategory, 10);
  const pips = Array.from(document.querySelectorAll('.pip'));
  const counterText = document.getElementById('votes-counter-text');

  function updateCounter(used) {
    pips.forEach((pip, i) => {
      pip.classList.toggle('filled', i < used);
    });
    const remaining = votesPerCategory - used;
    if (counterText) {
      counterText.textContent =
        remaining === 0
          ? 'No votes left'
          : remaining === 1
          ? '1 vote left'
          : `${remaining} votes left`;
    }

    document.querySelectorAll('.vote-card').forEach(card => {
      const selected = card.classList.contains('selected');
      card.classList.toggle('disabled', remaining === 0 && !selected);
    });
  }

  grid.addEventListener('click', function (e) {
    const card = e.target.closest('.vote-card');
    if (!card || card.classList.contains('disabled')) return;

    const beerId = card.dataset.beerId;
    const currentlySelected = card.classList.contains('selected');

    fetch(`/vote/${categoryId}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ beer_id: beerId }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          if (data.error.toLowerCase().includes('no votes')) {
            card.classList.add('disabled');
          }
          return;
        }
        card.classList.toggle('selected', data.voted);
        updateCounter(data.votes_used);
      })
      .catch(() => {});
  });
})();

/* ── Confirm dialogs ───────────────────────────────────────────────────── */
(function () {
  document.querySelectorAll('[data-confirm-trigger]').forEach(btn => {
    btn.addEventListener('click', function () {
      const targetId = this.dataset.confirmTrigger;
      const overlay = document.getElementById(targetId);
      if (overlay) overlay.classList.add('open');
    });
  });

  document.querySelectorAll('[data-confirm-cancel]').forEach(btn => {
    btn.addEventListener('click', function () {
      const targetId = this.dataset.confirmCancel;
      const overlay = document.getElementById(targetId);
      if (overlay) overlay.classList.remove('open');
    });
  });
})();
