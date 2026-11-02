/* Your Favorite Roofing — interactions
   No dependencies, no build step. The scroll effects live in motion.js; this
   file only handles things a visitor clicks, types or drags. */

(function () {
  'use strict';

  var doc = document;

  /* ------------------------------------------------------------------
     header: solid once the hero starts leaving
     ------------------------------------------------------------------ */

  (function header() {
    var el = doc.querySelector('[data-header]');
    if (!el) return;

    var ticking = false;
    function update() {
      ticking = false;
      el.classList.toggle('is-stuck', window.scrollY > 40);
    }
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }, { passive: true });
    update();
  })();

  /* ------------------------------------------------------------------
     mobile navigation
     ------------------------------------------------------------------ */

  (function navigation() {
    var toggle = doc.querySelector('.nav-toggle');
    var nav = doc.getElementById('site-nav');
    if (!toggle || !nav) return;

    function setOpen(open) {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      nav.classList.toggle('is-open', open);
      doc.body.classList.toggle('nav-open', open);
    }

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false);
    });

    doc.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });

    // A desktop resize should never leave the panel stuck open.
    window.addEventListener('resize', function () {
      if (window.innerWidth > 980) setOpen(false);
    });
  })();

  /* ------------------------------------------------------------------
     scrolling navigation state
     ------------------------------------------------------------------ */

  (function scrollSpy() {
    if (!('IntersectionObserver' in window)) return;
    var links = Array.prototype.slice.call(doc.querySelectorAll('#site-nav a[href^="#"]'));
    if (!links.length) return;

    var map = {};
    var sections = [];
    links.forEach(function (link) {
      var section = doc.querySelector(link.getAttribute('href'));
      if (!section) return;
      map[section.id] = link;
      sections.push(section);
    });

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (link) { link.classList.remove('is-active'); });
        var link = map[entry.target.id];
        if (link) link.classList.add('is-active');
      });
    }, { rootMargin: '-45% 0px -50% 0px' });

    sections.forEach(function (section) { observer.observe(section); });

    // the hero has no nav item of its own, so clear the highlight while it
    // still owns the screen
    var hero = doc.querySelector('.hero');
    if (hero) {
      new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) {
          links.forEach(function (link) { link.classList.remove('is-active'); });
        }
      }, { rootMargin: '-30% 0px -60% 0px' }).observe(hero);
    }
  })();

  /* ------------------------------------------------------------------
     roof anatomy: list drives the diagram
     ------------------------------------------------------------------ */

  (function anatomy() {
    var grid = doc.querySelector('[data-anatomy]');
    if (!grid) return;

    var buttons = Array.prototype.slice.call(grid.querySelectorAll('.part-btn'));
    var panels = Array.prototype.slice.call(grid.querySelectorAll('[data-panel]'));
    var parts = Array.prototype.slice.call(grid.querySelectorAll('.part'));
    var markers = Array.prototype.slice.call(grid.querySelectorAll('.marker'));
    if (!buttons.length) return;

    function show(key) {
      grid.setAttribute('data-active', key);

      buttons.forEach(function (button) {
        var on = button.getAttribute('data-target') === key;
        button.classList.toggle('is-on', on);
        button.setAttribute('aria-selected', String(on));
      });

      panels.forEach(function (panel) {
        panel.hidden = panel.getAttribute('data-panel') !== key;
      });

      parts.forEach(function (part) {
        var on = part.getAttribute('data-part') === key;
        part.classList.toggle('is-active', on);
        part.classList.toggle('is-dim', !on);
      });

      markers.forEach(function (marker) {
        marker.classList.toggle('is-on', marker.getAttribute('data-part') === key);
      });
    }

    // the numbered chips on the diagram are a second way in
    markers.forEach(function (marker) {
      marker.addEventListener('click', function () {
        show(marker.getAttribute('data-part'));
      });
    });

    buttons.forEach(function (button, index) {
      button.addEventListener('click', function () {
        show(button.getAttribute('data-target'));
      });

      button.addEventListener('keydown', function (event) {
        var next = null;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = index + 1;
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = index - 1;
        if (next === null) return;
        event.preventDefault();
        var target = buttons[(next + buttons.length) % buttons.length];
        target.focus();
        show(target.getAttribute('data-target'));
      });
    });

    show(buttons[0].getAttribute('data-target'));
  })();

  /* ------------------------------------------------------------------
     before / after slider
     ------------------------------------------------------------------ */

  (function beforeAfter() {
    var fig = doc.querySelector('[data-ba]');
    if (!fig) return;

    var handle = fig.querySelector('[data-ba-handle]');
    var MIN = 4;
    var MAX = 96;
    var value = 52;
    var dragging = false;

    var clamp = function (n) { return n < MIN ? MIN : n > MAX ? MAX : n; };

    function paint(next) {
      value = clamp(next);
      fig.style.setProperty('--split', value + '%');
      if (handle) handle.setAttribute('aria-valuenow', String(Math.round(value)));
    }

    function fromPointer(clientX) {
      var box = fig.getBoundingClientRect();
      if (!box.width) return;
      paint(((clientX - box.left) / box.width) * 100);
    }

    fig.addEventListener('pointerdown', function (event) {
      if (event.button !== 0 && event.pointerType === 'mouse') return;
      dragging = true;
      fig.classList.add('is-dragging');
      if (fig.setPointerCapture) {
        try { fig.setPointerCapture(event.pointerId); } catch (err) { /* ignore */ }
      }
      fromPointer(event.clientX);
      event.preventDefault();
    });

    fig.addEventListener('pointermove', function (event) {
      if (!dragging) return;
      fromPointer(event.clientX);
    });

    function end(event) {
      if (!dragging) return;
      dragging = false;
      fig.classList.remove('is-dragging');
      if (fig.releasePointerCapture && event && event.pointerId !== undefined) {
        try { fig.releasePointerCapture(event.pointerId); } catch (err) { /* ignore */ }
      }
    }
    fig.addEventListener('pointerup', end);
    fig.addEventListener('pointercancel', end);
    fig.addEventListener('pointerleave', function (event) {
      if (event.buttons === 0) end(event);
    });

    if (handle) {
      handle.addEventListener('keydown', function (event) {
        var step = event.shiftKey ? 10 : 2;
        if (event.key === 'ArrowLeft') { paint(value - step); event.preventDefault(); }
        else if (event.key === 'ArrowRight') { paint(value + step); event.preventDefault(); }
        else if (event.key === 'Home') { paint(MIN); event.preventDefault(); }
        else if (event.key === 'End') { paint(MAX); event.preventDefault(); }
      });
    }

    paint(value);
  })();

  /* ------------------------------------------------------------------
     quote form
     ------------------------------------------------------------------
     Set formEndpoint to a URL that accepts JSON to collect submissions
     server-side. Left empty, the form composes an email in the visitor's
     mail app instead — honest, and nothing to configure. */

  (function quoteForm() {
    var form = doc.querySelector('[data-quote-form]');
    if (!form) return;

    var status = form.querySelector('[data-status]');
    var submit = form.querySelector('[data-submit]');
    var EMAIL = 'hello@yourfavoriteroofing.example';

    function setStatus(message, kind) {
      if (!status) return;
      status.textContent = message;
      status.classList.toggle('is-error', kind === 'error');
      status.classList.toggle('is-ok', kind === 'ok');
    }

    function firstInvalid() {
      var fields = Array.prototype.slice.call(form.querySelectorAll('[required]'));
      for (var i = 0; i < fields.length; i++) {
        if (!fields[i].value.trim()) {
          return { field: fields[i], message: 'Please fill in your name, phone, address and the type of job.' };
        }
      }
      var email = form.querySelector('#q-email');
      if (email && email.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim())) {
        return { field: email, message: 'That email address doesn\u2019t look right \u2014 or leave it blank.' };
      }
      return null;
    }

    function body() {
      var data = new FormData(form);
      var lines = [];
      var labels = {
        name: 'Name',
        phone: 'Phone',
        email: 'Email',
        address: 'Address or ZIP',
        job: 'Job',
        message: 'Details'
      };
      Object.keys(labels).forEach(function (key) {
        var value = (data.get(key) || '').toString().trim();
        if (value) lines.push(labels[key] + ': ' + value);
      });
      lines.push('', 'Sent from yourfavoriteroofing.example');
      return lines.join('\n');
    }

    form.addEventListener('submit', function (event) {
      event.preventDefault();

      var honeypot = form.querySelector('[name="company"]');
      if (honeypot && honeypot.value) {
        setStatus('Thanks \u2014 we\u2019ll be in touch.', 'ok');
        return;
      }

      var bad = firstInvalid();
      if (bad) {
        bad.field.focus();
        setStatus(bad.message, 'error');
        return;
      }

      var endpoint = form.getAttribute('data-endpoint');
      var name = (form.querySelector('#q-name') || {}).value || '';

      if (endpoint) {
        if (submit) submit.disabled = true;
        setStatus('Sending…', '');
        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(Object.fromEntries(new FormData(form)))
        })
          .then(function (response) {
            if (!response.ok) throw new Error('Bad response');
            form.reset();
            setStatus('Thanks, ' + name.split(' ')[0] + '. We have it \u2014 we\u2019ll call before we come out.', 'ok');
          })
          .catch(function () {
            setStatus('That didn\u2019t send. Please call instead \u2014 the number is at the top of the page.', 'error');
          })
          .then(function () {
            if (submit) submit.disabled = false;
          });
        return;
      }

      var subject = 'Roof inspection request — ' + name;
      window.location.href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body());
      setStatus('Opening your mail app with the details. If nothing happens, call us instead.', 'ok');
    });
  })();

  /* ------------------------------------------------------------------
     odds and ends
     ------------------------------------------------------------------ */

  (function year() {
    var el = doc.querySelector('[data-year]');
    if (el) el.textContent = String(new Date().getFullYear());
  })();

  // close the mobile menu if the viewport changes under it
  doc.addEventListener('click', function (event) {
    var link = event.target.closest('a[href^="#"]');
    if (!link) return;
    var target = doc.querySelector(link.getAttribute('href'));
    if (!target) return;
    // keep focus meaningful after a jump without fighting scroll-padding
    target.setAttribute('tabindex', '-1');
    setTimeout(function () { target.focus({ preventScroll: true }); }, 400);
  });
})();
