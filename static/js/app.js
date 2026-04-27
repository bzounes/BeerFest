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
  const pip = document.querySelector('.pip');
  const counterText = document.getElementById('votes-counter-text');

  function updateCounter(used) {
    if (pip) pip.classList.toggle('filled', used > 0);
    if (counterText) {
      counterText.textContent = used > 0 ? 'Vote cast' : 'Not yet voted';
    }
    const remaining = votesPerCategory - used;
    document.querySelectorAll('.vote-card').forEach(card => {
      card.classList.toggle('disabled', remaining === 0 && !card.classList.contains('selected'));
    });
  }

  function doToggle(beerId, onSuccess) {
    fetch(`/vote/${categoryId}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ beer_id: beerId }),
    })
      .then(r => r.json())
      .then(data => { if (!data.error) onSuccess(data); })
      .catch(() => {});
  }

  grid.addEventListener('click', function (e) {
    const card = e.target.closest('.vote-card');
    if (!card) return;

    const isSelected = card.classList.contains('selected');
    const isDisabled = card.classList.contains('disabled');

    // Single-vote swap: clicking a different beer auto-moves the vote
    if (!isSelected && !isDisabled && votesPerCategory === 1) {
      const current = grid.querySelector('.vote-card.selected');
      if (current) {
        doToggle(current.dataset.beerId, () => {
          current.classList.remove('selected');
          doToggle(card.dataset.beerId, data => {
            card.classList.add('selected');
            updateCounter(data.votes_used);
          });
        });
        return;
      }
    }

    if (isDisabled) return;

    doToggle(card.dataset.beerId, data => {
      card.classList.toggle('selected', data.voted);
      updateCounter(data.votes_used);
    });
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
