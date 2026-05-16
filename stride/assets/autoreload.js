/**
 * Auto-reload when the server has been redeployed.
 *
 * Strategy: hash /_dash-dependencies on load, then re-check every 30 s
 * and on tab focus. If the hash changes the server has new callback
 * fingerprints → reload silently. On any 500 from /_dash-update-component
 * we also run an immediate check so stale-tab errors self-heal within
 * one failed request rather than requiring a manual hard-refresh.
 */
(function () {
  "use strict";

  var baselineHash = null;
  var reloading = false;

  function djb2(str) {
    var hash = 5381;
    for (var i = 0; i < str.length; i++) {
      hash = ((hash << 5) + hash) ^ str.charCodeAt(i);
      hash |= 0;
    }
    return hash;
  }

  function checkAndReload() {
    if (reloading) return;
    fetch("/_dash-dependencies", { cache: "no-cache" })
      .then(function (r) { return r.text(); })
      .then(function (body) {
        var h = djb2(body);
        if (baselineHash === null) {
          baselineHash = h;
        } else if (h !== baselineHash) {
          reloading = true;
          window.location.reload();
        }
      })
      .catch(function () {});
  }

  // Establish baseline immediately
  checkAndReload();

  // Poll every 30 s
  setInterval(checkAndReload, 30000);

  // Re-check whenever the tab becomes visible (catches users returning after a deploy)
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") checkAndReload();
  });

  // On any 500 from a Dash callback, immediately re-check.
  // If the server was updated, hash will have changed → reload.
  // If it's a genuine Python error in a callback, hash won't change → no reload.
  var _origFetch = window.fetch;
  window.fetch = function (url, options) {
    return _origFetch(url, options).then(function (response) {
      if (
        response.status === 500 &&
        typeof url === "string" &&
        url.indexOf("_dash-update-component") !== -1
      ) {
        checkAndReload();
      }
      return response;
    });
  };
})();
