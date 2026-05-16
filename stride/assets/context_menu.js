/**
 * Custom right-click context menu for task cards.
 *
 * Intercepts contextmenu on .card-wrapper elements and shows a Stride-specific
 * menu. Actions work by programmatically clicking the existing Dash buttons
 * already in the DOM — no new Python callbacks needed.
 *
 * Right-clicking anywhere outside a card shows the normal browser menu.
 */
(function () {
  "use strict";

  var menu = null;
  var activeWrapper = null;

  // ── Build the menu element once ──────────────────────────────────────────
  function ensureMenu() {
    if (menu) return;

    menu = document.createElement("div");
    menu.id = "stride-ctx-menu";
    menu.className = "stride-ctx-menu";
    menu.innerHTML = [
      '<button class="stride-ctx-item" data-action="open">',
        '<span class="stride-ctx-icon">↗</span> Open details',
      "</button>",
      '<button class="stride-ctx-item" data-action="move">',
        '<span class="stride-ctx-icon">→</span> Move to…',
      "</button>",
      '<button class="stride-ctx-item" id="stride-ctx-done" data-action="done">',
        '<span class="stride-ctx-icon">✓</span> Mark as done',
      "</button>",
    ].join("");

    menu.style.display = "none";
    document.body.appendChild(menu);

    // Stop clicks inside the menu from closing it via the outside-click handler
    menu.addEventListener("mousedown", function (e) {
      e.stopPropagation();
    });

    menu.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-action]");
      if (!btn || !activeWrapper) return;
      dispatch(btn.dataset.action, activeWrapper);
      hide();
    });
  }

  // ── Dispatch to existing Dash buttons ────────────────────────────────────
  function dispatch(action, wrapper) {
    if (action === "open") {
      var card = wrapper.querySelector(".task-card");
      if (card) card.click();

    } else if (action === "move") {
      var flyout = wrapper.querySelector(".move-menu-dropdown");
      if (flyout) {
        // Old CSS hover flyout — reveal it via a class, close on next click outside
        var mw = wrapper.querySelector(".card-move-wrapper");
        if (mw) {
          mw.classList.add("stride-flyout-open");
          document.addEventListener("mousedown", function closeFlyout() {
            mw.classList.remove("stride-flyout-open");
            document.removeEventListener("mousedown", closeFlyout, true);
          }, true);
        }
      } else {
        // New modal button (PR #25+)
        var moveBtn = wrapper.querySelector(".card-move-btn");
        if (moveBtn) moveBtn.click();
      }

    } else if (action === "done") {
      var checkbox = wrapper.querySelector("button.card-checkbox, button.card-checkbox--done");
      if (checkbox) checkbox.click();
    }
  }

  // ── Show / hide ───────────────────────────────────────────────────────────
  function show(x, y, wrapper) {
    ensureMenu();
    activeWrapper = wrapper;

    // Update done/reopen label based on current card state
    var isDone = !!wrapper.querySelector(".card-checkbox--done");
    var doneBtn = document.getElementById("stride-ctx-done");
    if (doneBtn) {
      var icon = doneBtn.querySelector(".stride-ctx-icon");
      doneBtn.innerHTML = "";
      var iconEl = document.createElement("span");
      iconEl.className = "stride-ctx-icon";
      iconEl.textContent = isDone ? "↩" : "✓";
      doneBtn.appendChild(iconEl);
      doneBtn.appendChild(document.createTextNode(" " + (isDone ? "Reopen task" : "Mark as done")));
    }

    menu.style.display = "block";
    menu.style.left = x + "px";
    menu.style.top = y + "px";

    // Clamp to viewport after layout
    requestAnimationFrame(function () {
      var rect = menu.getBoundingClientRect();
      if (rect.right > window.innerWidth - 8) {
        menu.style.left = Math.max(8, x - rect.width) + "px";
      }
      if (rect.bottom > window.innerHeight - 8) {
        menu.style.top = Math.max(8, y - rect.height) + "px";
      }
    });
  }

  function hide() {
    if (menu) menu.style.display = "none";
    activeWrapper = null;
  }

  // ── Event listeners ───────────────────────────────────────────────────────
  document.addEventListener("contextmenu", function (e) {
    var wrapper = e.target.closest(".card-wrapper");
    if (!wrapper) {
      // Mantine's drawer overlay captures pointer events — temporarily pierce it
      // so elementFromPoint can find the card underneath.
      var el = e.target;
      var origPE = el.style.pointerEvents;
      el.style.pointerEvents = "none";
      var under = document.elementFromPoint(e.clientX, e.clientY);
      el.style.pointerEvents = origPE;
      if (under) wrapper = under.closest(".card-wrapper");
    }
    if (!wrapper) {
      hide();
      return; // let the browser show its default menu elsewhere
    }
    e.preventDefault();
    show(e.clientX, e.clientY, wrapper);
  });

  // Dismiss on any click outside the menu
  document.addEventListener("mousedown", function (e) {
    if (menu && menu.style.display !== "none" && !menu.contains(e.target)) {
      hide();
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hide();
  });

  // Dismiss on scroll (board scrolls horizontally)
  window.addEventListener("scroll", hide, true);
})();
