(function () {
  // Event delegation: one listener handles all expand buttons across all day columns,
  // even after Dash re-renders the board and replaces DOM nodes.
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.btn-expand-composer');
    if (!btn) return;

    var composer = btn.closest('.composer');
    if (!composer) return;

    var pickers = composer.querySelector('.composer-pickers');
    if (!pickers) return;

    var expanded = pickers.style.display === 'flex' || pickers.style.display === 'block';
    pickers.style.display = expanded ? 'none' : 'flex';
    btn.textContent = expanded ? '▾ Details' : '▴ Details';
  });
})();
