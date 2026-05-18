/* Stride drag-and-drop bridge
 *
 * Uses HTML5 native drag events with event delegation so it works on
 * dynamically re-rendered card lists. On drop, writes task_id + to_day_key
 * into the Dash store "store-dnd-drop" via window.dash_clientside.set_props
 * (Dash 2.9+). A server callback handles the actual move_task call.
 */
(function () {
  var dragging = null;

  function clearDropHighlights() {
    document.querySelectorAll('.day-column--drop-active').forEach(function (el) {
      el.classList.remove('day-column--drop-active');
    });
  }

  // Use capture phase (true) so these listeners fire BEFORE React 18's event
  // delegation, which attaches to the React root element and can swallow drag
  // events before they bubble to document-level bubble-phase listeners.
  document.addEventListener('dragstart', function (e) {
    var wrapper = e.target.closest('[data-task-id]');
    if (!wrapper) return;
    dragging = wrapper.dataset.taskId;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', dragging);
    }
    // Defer adding .dragging so the drag ghost captures the un-dimmed card
    setTimeout(function () { wrapper.classList.add('dragging'); }, 0);
  }, true);

  document.addEventListener('dragend', function (e) {
    var wrapper = e.target.closest('[data-task-id]');
    if (wrapper) wrapper.classList.remove('dragging');
    clearDropHighlights();
    dragging = null;
  }, true);

  document.addEventListener('dragover', function (e) {
    if (!dragging) return;
    var col = e.target.closest('[data-drop-day]');
    if (!col) return;
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
    clearDropHighlights();
    col.classList.add('day-column--drop-active');
  }, true);

  document.addEventListener('dragleave', function (e) {
    var col = e.target.closest('[data-drop-day]');
    if (!col) return;
    // Only clear if leaving the column entirely (not entering a child element)
    if (!col.contains(e.relatedTarget)) {
      col.classList.remove('day-column--drop-active');
    }
  }, true);

  document.addEventListener('drop', function (e) {
    var col = e.target.closest('[data-drop-day]');
    if (!col || !dragging) return;
    e.preventDefault();
    col.classList.remove('day-column--drop-active');
    var toDay = col.dataset.dropDay;
    if (window.dash_clientside && window.dash_clientside.set_props) {
      window.dash_clientside.set_props('store-dnd-drop', {
        data: { task_id: dragging, to_day_key: toDay, ts: Date.now() }
      });
    }
    dragging = null;
  }, true);
})();
