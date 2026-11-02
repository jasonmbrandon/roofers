/* Your Favorite Roofing — motion layer
   Vanilla JS, no dependencies. Everything is scroll-driven and every effect
   is skipped under prefers-reduced-motion, which leaves the page static but
   complete. The build scene is generated here so the HTML stays readable. */

(function () {
  'use strict';

  var doc = document;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function clamp(n, min, max) {
    return n < min ? min : n > max ? max : n;
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function svgEl(name) {
    return doc.createElementNS('http://www.w3.org/2000/svg', name);
  }

  /* ------------------------------------------------------------------
     one loop for every scroll effect
     ------------------------------------------------------------------ */

  var tasks = [];
  var ticking = false;

  function run() {
    ticking = false;
    for (var i = 0; i < tasks.length; i++) tasks[i]();
  }

  function tick() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(run);
  }

  window.addEventListener('scroll', tick, { passive: true });
  window.addEventListener('resize', tick);

  /* ------------------------------------------------------------------
     reading progress
     ------------------------------------------------------------------ */

  (function progress() {
    if (reduce) return;
    var bar = doc.createElement('div');
    bar.className = 'scroll-progress';
    bar.setAttribute('aria-hidden', 'true');
    var fill = doc.createElement('span');
    bar.appendChild(fill);
    doc.body.appendChild(bar);

    tasks.push(function () {
      var max = doc.documentElement.scrollHeight - window.innerHeight;
      var value = max > 0 ? clamp(window.scrollY / max, 0, 1) : 0;
      fill.style.transform = 'scaleX(' + value.toFixed(4) + ')';
    });
  })();

  /* ------------------------------------------------------------------
     reveals
     ------------------------------------------------------------------ */

  (function reveals() {
    var items = Array.prototype.slice.call(doc.querySelectorAll('.reveal'));
    if (!items.length) return;

    if (reduce || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });

    items.forEach(function (el) { observer.observe(el); });

    // Never leave content invisible if the observer never fires (hidden views,
    // restored scroll positions, very tall screenshots).
    window.setTimeout(function () {
      items.forEach(function (el) {
        var box = el.getBoundingClientRect();
        if (box.top < window.innerHeight) el.classList.add('is-in');
      });
    }, 2200);
  })();

  /* ------------------------------------------------------------------
     hero parallax
     ------------------------------------------------------------------ */

  (function heroParallax() {
    if (reduce) return;
    var hero = doc.querySelector('.hero');
    var layers = Array.prototype.slice.call(doc.querySelectorAll('.hero-layer'));
    if (!hero || !layers.length) return;

    tasks.push(function () {
      var y = window.scrollY;
      if (y > window.innerHeight * 1.6) return;
      layers.forEach(function (layer) {
        var depth = parseFloat(layer.getAttribute('data-depth')) || 0;
        if (depth < 0.2) return; // the sky and sun stay put
        var offset = (y * depth * 0.18).toFixed(1);
        layer.style.transform = 'translate3d(0,' + offset + 'px,0)';
      });
    });
  })();

  /* ------------------------------------------------------------------
     cards that lean toward the pointer
     ------------------------------------------------------------------
     Any element with data-tilt lifts off the grid and tips a few degrees
     toward the cursor, with a sheen that follows it (--mx/--my feed the CSS
     radial gradient). Pointer only: touch and reduced motion get the plain
     4px lift from the stylesheet. */

  (function pointerTilt() {
    if (reduce) return;
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    var cards = Array.prototype.slice.call(doc.querySelectorAll('[data-tilt]'));
    if (!cards.length) return;

    var TILT = 5.5;

    cards.forEach(function (card) {
      var box = null;

      function paint(x, y) {
        if (!box || !box.width || !box.height) return;
        var px = clamp((x - box.left) / box.width, 0, 1);
        var py = clamp((y - box.top) / box.height, 0, 1);

        card.style.setProperty('--mx', (px * 100).toFixed(1) + '%');
        card.style.setProperty('--my', (py * 100).toFixed(1) + '%');
        card.style.transform =
          'perspective(900px)' +
          ' rotateX(' + ((0.5 - py) * TILT).toFixed(2) + 'deg)' +
          ' rotateY(' + ((px - 0.5) * TILT * 1.15).toFixed(2) + 'deg)' +
          ' translateY(-6px)';
      }

      card.addEventListener('pointerenter', function (event) {
        box = card.getBoundingClientRect();
        card.style.transition = 'transform .18s var(--ease), box-shadow .45s var(--ease), border-color .45s var(--ease)';
        card.classList.add('is-tilt');
        paint(event.clientX, event.clientY);
      });

      // Written straight to the element: a card must not freeze when the tab
      // throttles requestAnimationFrame.
      card.addEventListener('pointermove', function (event) {
        if (event.pointerType && event.pointerType !== 'mouse' && event.pointerType !== 'pen') return;
        paint(event.clientX, event.clientY);
      });

      card.addEventListener('pointerleave', function () {
        card.classList.remove('is-tilt');
        card.style.transition = 'transform .42s var(--ease), box-shadow .45s var(--ease), border-color .45s var(--ease)';
        card.style.transform = '';
        box = null;
      });
    });
  })();

  /* ------------------------------------------------------------------
     the build scene
     ═══════════════════════════════════════════════════════════════════ */

  (function buildScene() {
    var section = doc.querySelector('[data-build]');
    if (!section) return;

    var oldRoof = section.querySelector('.b-old');
    var felt = section.querySelector('.b-felt');
    var feltLines = section.querySelector('.b-felt-lines');
    var flash = section.querySelector('.b-flash');
    var ridge = section.querySelector('.b-ridge');
    var rowsHost = section.querySelector('.b-courses');
    var badge = section.querySelector('[data-badge]');
    var meter = section.querySelector('[data-meter]');
    var steps = Array.prototype.slice.call(section.querySelectorAll('.build-steps li'));

    var ROWS = 9;
    var ROW_H = 44;
    var TAB_W = 76;
    var PLANE_W = 578;

    var rows = [];

    if (rowsHost) {
      rowsHost.innerHTML = '';
      for (var i = 0; i < ROWS; i++) {
        var group = svgEl('g');
        group.setAttribute('class', 'course');
        group.setAttribute('data-row', String(i));

        var top = -ROW_H * (i + 1);
        var stagger = i % 2 ? TAB_W / 2 : 0;
        var base = i % 2 ? '#313c46' : '#2b3540';

        for (var x = -stagger - TAB_W; x < PLANE_W + TAB_W; x += TAB_W) {
          var tab = svgEl('rect');
          tab.setAttribute('x', String(x));
          tab.setAttribute('y', String(top));
          tab.setAttribute('width', String(TAB_W));
          tab.setAttribute('height', String(ROW_H));
          tab.setAttribute('fill', base);
          group.appendChild(tab);

          var joint = svgEl('path');
          joint.setAttribute('d', 'M' + x + ' ' + (top + ROW_H) + 'v-13');
          joint.setAttribute('stroke', '#151d24');
          joint.setAttribute('stroke-width', '2');
          group.appendChild(joint);
        }

        var edge = svgEl('rect');
        edge.setAttribute('x', String(-TAB_W));
        edge.setAttribute('y', String(top + ROW_H - 7));
        edge.setAttribute('width', String(PLANE_W + TAB_W * 3));
        edge.setAttribute('height', '7');
        edge.setAttribute('fill', '#101820');
        edge.setAttribute('opacity', '0.65');
        group.appendChild(edge);

        var lip = svgEl('rect');
        lip.setAttribute('x', String(-TAB_W));
        lip.setAttribute('y', String(top + ROW_H - 2));
        lip.setAttribute('width', String(PLANE_W + TAB_W * 3));
        lip.setAttribute('height', '2');
        lip.setAttribute('fill', '#3d4954');
        group.appendChild(lip);

        rowsHost.appendChild(group);
        rows.push(group);
      }
    }

    // every state is written as an inline style: stylesheet rules set the
    // pre-paint state, and inline wins over them on the first frame.
    function paint(p) {
      if (oldRoof) {
        var strip = clamp(p / 0.17, 0, 1);
        oldRoof.style.opacity = (1 - strip).toFixed(3);
        oldRoof.style.transform = 'translateY(' + (strip * 120).toFixed(1) + 'px)';
      }

      if (felt) {
        var unroll = easeOutCubic(clamp((p - 0.15) / 0.26, 0, 1));
        felt.style.clipPath = 'inset(0 ' + ((1 - unroll) * 100).toFixed(2) + '% 0 0)';
      }
      if (feltLines) {
        feltLines.style.opacity = clamp((p - 0.32) / 0.08, 0, 1).toFixed(3);
      }

      if (flash) {
        flash.style.opacity = clamp((p - 0.36) / 0.08, 0, 1).toFixed(3);
      }

      for (var i = 0; i < rows.length; i++) {
        var start = 0.44 + i * 0.052;
        var t = easeOutCubic(clamp((p - start) / 0.075, 0, 1));
        rows[i].style.opacity = t.toFixed(3);
        rows[i].style.transform = 'translateY(' + (30 * (1 - t)).toFixed(2) + 'px)';
      }

      if (ridge) {
        var cap = easeOutCubic(clamp((p - 0.885) / 0.075, 0, 1));
        ridge.style.opacity = cap.toFixed(3);
        ridge.style.transform = 'translateY(' + (-34 * (1 - cap)).toFixed(1) + 'px)';
      }

      var stage = p < 0.2 ? 0 : p < 0.42 ? 1 : p < 0.86 ? 2 : 3;
      if (badge) badge.textContent = '0' + (stage + 1);
      steps.forEach(function (li, index) {
        li.classList.toggle('is-on', index === stage);
      });
      if (meter) meter.style.transform = 'scaleX(' + clamp(p, 0.02, 1).toFixed(4) + ')';
    }

    function progressOf() {
      var box = section.getBoundingClientRect();
      var travel = box.height - window.innerHeight;
      if (travel <= 0) return 0;
      return clamp(-box.top / travel, 0, 1);
    }

    var mobile = window.matchMedia('(max-width: 980px)');
    var stageFromView = 0;

    // Phones get the scene driven by the step that is currently on screen,
    // because the section is not pinned there.
    if ('IntersectionObserver' in window) {
      var stepObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var index = steps.indexOf(entry.target);
          if (index >= 0) stageFromView = index;
        });
      }, { rootMargin: '-40% 0px -40% 0px' });

      steps.forEach(function (li) { stepObserver.observe(li); });
    }

    var last = -1;

    function update() {
      var p;
      if (mobile.matches) {
        p = [0.02, 0.3, 0.66, 0.98][stageFromView] || 0;
      } else {
        p = progressOf();
      }
      if (Math.abs(p - last) < 0.0015) return;
      last = p;
      paint(p);
    }

    if (reduce) {
      paint(1);
      return;
    }

    tasks.push(update);
    update();
  })();

  /* ------------------------------------------------------------------
     process rail — a hairline that fills as the steps go by
     ------------------------------------------------------------------ */

  (function processRail() {
    if (reduce) return;
    var section = doc.querySelector('#process');
    var rail = doc.querySelector('[data-rail]');
    if (!section || !rail) return;

    tasks.push(function () {
      var box = section.getBoundingClientRect();
      if (box.bottom < 0 || box.top > window.innerHeight) return;
      var span = box.height + window.innerHeight * 0.5;
      var p = clamp((window.innerHeight * 0.75 - box.top) / span, 0, 1);
      rail.style.transform = 'scaleX(' + p.toFixed(4) + ')';
    });
  })();

  /* ------------------------------------------------------------------
     first frame
     ------------------------------------------------------------------ */

  if (doc.readyState === 'loading') {
    doc.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
