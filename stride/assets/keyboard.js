(function () {
  var IGNORE_TAGS = ['INPUT', 'TEXTAREA', 'SELECT'];

  document.addEventListener('keydown', function (e) {
    if (IGNORE_TAGS.includes(e.target.tagName)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    var action = null;
    switch (e.key) {
      case 'Escape': action = 'close';       break;
      case 'd':      action = 'toggle-done'; break;
      case 'e':      action = 'open-drawer'; break;
    }
    if (!action) return;
    e.preventDefault();

    window.dash_clientside.set_props('store-kb-action', {
      data: { action: action, ts: Date.now() }
    });
  });
})();
