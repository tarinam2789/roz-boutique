// Roz — small progressive-enhancement helpers

function rozOpenDrawer() {
  document.getElementById('nav-drawer').classList.add('open');
  document.getElementById('nav-drawer-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function rozCloseDrawer() {
  document.getElementById('nav-drawer').classList.remove('open');
  document.getElementById('nav-drawer-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function rozShowGalleryItem(idx) {
  document.querySelectorAll('.gallery-item').forEach(function (el) {
    var isActive = el.getAttribute('data-gallery-index') === String(idx);
    el.classList.toggle('active', isActive);
    // pause any playing video when it's no longer the active item
    if (!isActive) {
      var vid = el.querySelector('video');
      if (vid) vid.pause();
    }
  });
  document.querySelectorAll('.gallery-thumb').forEach(function (el) {
    el.classList.toggle('active', el.getAttribute('data-gallery-index') === String(idx));
  });
}

document.addEventListener('DOMContentLoaded', function () {
  // Size pill visual state (radio inputs already handle :has() styling,
  // this adds a fallback 'active' class for broader browser support)
  document.querySelectorAll('.size-pill input[type=radio]').forEach(function (input) {
    input.addEventListener('change', function () {
      var group = input.closest('.size-options');
      if (group) {
        group.querySelectorAll('.size-pill').forEach(function (pill) { pill.classList.remove('active'); });
      }
      input.closest('.size-pill').classList.add('active');
    });
  });

  // Close modals on overlay click or Escape key
  document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(function (o) { o.classList.remove('open'); });
      rozCloseDrawer();
    }
  });

  // Auto-dismiss flash messages
  document.querySelectorAll('.flash').forEach(function (el) {
    setTimeout(function () { el.style.transition = 'opacity .5s'; el.style.opacity = '0'; }, 4500);
  });
});
