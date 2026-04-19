/* OinkFarm Sprint Dashboard — progressive enhancement.
   All page function works without JS; this adds:
     - Live clock ticker
     - Auto-refresh of data.json (every 60s) with soft UI updates
     - Tab switching (Narrative / Plans / OinkV Audits)
     - Expand/collapse persistence for task timelines
*/
(function () {
  'use strict';

  // -----------------------------------------------------------------------
  // Clock ticker — updates UTC + CEST every second.
  // -----------------------------------------------------------------------
  function pad(n) { return String(n).padStart(2, '0'); }
  function fmtUTC(d) {
    return (
      d.getUTCFullYear() + '-' +
      pad(d.getUTCMonth() + 1) + '-' +
      pad(d.getUTCDate()) + 'T' +
      pad(d.getUTCHours()) + ':' +
      pad(d.getUTCMinutes()) + ':' +
      pad(d.getUTCSeconds()) + 'Z'
    );
  }
  function fmtCEST(d) {
    // CEST = UTC+2
    var t = new Date(d.getTime() + 2 * 3600 * 1000);
    return (
      t.getUTCFullYear() + '-' +
      pad(t.getUTCMonth() + 1) + '-' +
      pad(t.getUTCDate()) + ' ' +
      pad(t.getUTCHours()) + ':' +
      pad(t.getUTCMinutes()) + ':' +
      pad(t.getUTCSeconds()) + ' CEST'
    );
  }

  function tick() {
    var now = new Date();
    var utc = document.getElementById('clock-utc');
    var cest = document.getElementById('clock-cest');
    if (utc) utc.textContent = fmtUTC(now);
    if (cest) cest.textContent = fmtCEST(now);
  }
  tick();
  setInterval(tick, 1000);

  // -----------------------------------------------------------------------
  // Tab switching.
  // -----------------------------------------------------------------------
  var tabs = document.querySelectorAll('.tab');
  tabs.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-tab');
      // Only toggle sibling tabs (same .tab-row).
      var row = btn.parentElement;
      row.querySelectorAll('.tab').forEach(function (b) {
        b.classList.remove('tab-active');
      });
      btn.classList.add('tab-active');
      // Panels live alongside the tab row's parent panel.
      var panel = row.closest('.panel');
      if (!panel) return;
      panel.querySelectorAll('.tab-panel').forEach(function (p) {
        p.classList.toggle('tab-panel-active', p.id === 'tab-' + id);
      });
    });
  });

  // -----------------------------------------------------------------------
  // Top-bar nav — Dashboard / Events in-page links, visual active state.
  // Phases / Tasks / GitHub are external links handled by browser.
  // -----------------------------------------------------------------------
  var navlinks = document.querySelectorAll('.navlink[data-nav]');
  navlinks.forEach(function (a) {
    a.addEventListener('click', function () {
      navlinks.forEach(function (n) { n.classList.remove('navlink-active'); });
      a.classList.add('navlink-active');
    });
  });

  // -----------------------------------------------------------------------
  // Persist open/closed state of each task timeline across refreshes.
  // -----------------------------------------------------------------------
  try {
    document.querySelectorAll('.task-timeline').forEach(function (det) {
      var parent = det.closest('[id]');
      if (!parent) return;
      var key = 'timeline:' + parent.id;
      if (localStorage.getItem(key) === '1') det.open = true;
      det.addEventListener('toggle', function () {
        localStorage.setItem(key, det.open ? '1' : '0');
      });
    });
  } catch (e) { /* localStorage may be blocked; ignore */ }

  // -----------------------------------------------------------------------
  // Auto-refresh: fetch data.json every 60s, reload the page if the
  // generated_at timestamp changed (i.e., the generator ran again).
  // -----------------------------------------------------------------------
  var INITIAL_GEN = document.body.getAttribute('data-generated') || '';
  var REFRESH_MS = 60 * 1000;
  var pill = document.getElementById('refresh-pill');
  function setPill(label, cls) {
    if (!pill) return;
    pill.innerHTML = '<span class="dot ' + cls + '"></span> ' + label;
  }

  function refresh() {
    setPill('checking…', 'dot-yellow');
    fetch('data.json?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        if (data.generated_at_utc && data.generated_at_utc !== INITIAL_GEN) {
          setPill('new data — reloading', 'dot-green');
          setTimeout(function () { location.reload(); }, 400);
        } else {
          setPill('auto', 'dot-green');
        }
      })
      .catch(function () { setPill('offline', 'dot-red'); });
  }
  setInterval(refresh, REFRESH_MS);
})();
