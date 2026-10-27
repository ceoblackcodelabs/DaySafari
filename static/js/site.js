(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // Mobile menu
  var toggle = $('.menu-toggle'), menu = $('#mobile-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var open = menu.hidden;
      menu.hidden = !open;
      toggle.setAttribute('aria-expanded', open);
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      $('.i-open', toggle).hidden = open;
      $('.i-close', toggle).hidden = !open;
    });
  }


  // Images whose file is missing disappear instead of showing a broken icon; empty sections hide too
  var dropBroken = function (img) {
    var box = img.closest('a') || img; box.remove();
    $$('[data-hide-if-empty]').forEach(function (sec) { if (!sec.querySelector('img')) sec.hidden = true; });
  };
  $$('img[data-hide-on-error]').forEach(function (img) {
    if (img.complete && img.naturalWidth === 0 && img.currentSrc) dropBroken(img);
    else img.addEventListener('error', function () { dropBroken(img); });
  });

  // Infinite logo marquee: clones the set until it is wider than the screen, then scrolls it forever
  $$('[data-marquee]').forEach(function (box) {
    var track = $('.marquee-track', box), set = $('.marquee-set', box);
    if (!track || !set || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) return;
    var build = function () {
      if (!set.children.length) return;
      var w = set.offsetWidth; if (!w) return;
      var copies = Math.max(1, Math.ceil(box.offsetWidth / w)) + 1;
      for (var i = 0; i < copies; i++) { var c = set.cloneNode(true); c.setAttribute('aria-hidden', 'true'); $$('a', c).forEach(function (a) { a.tabIndex = -1; }); track.appendChild(c); }
      box.style.setProperty('--shift', w + 'px'); box.style.setProperty('--dur', Math.max(12, w / 45) + 's'); box.classList.add('run');
    };
    var imgs = $$('img', set), left = imgs.length;
    if (!left) return;
    var done = function () { if (--left === 0) setTimeout(build, 60); };
    imgs.forEach(function (im) { if (im.complete) done(); else { im.addEventListener('load', done); im.addEventListener('error', done); } });
  });

  // Flash messages, auto-submit selects
  $$('.flash-x').forEach(function (b) { b.addEventListener('click', function () { b.parentNode.remove(); }); });
  $$('[data-autosubmit]').forEach(function (el) { el.addEventListener('change', function () { el.form.submit(); }); });

  // Generic dialogs (quick-lead popup + ad popup)
  var storeGet = function (k) { try { return JSON.parse(localStorage.getItem(k) || '{}'); } catch (e) { return {}; } };
  var storePut = function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  var DAY = 86400000;
  var openOverlay = function (ov) { ov.hidden = false; ov.classList.add('active'); var f = $('input,textarea', ov); if (f) setTimeout(function () { f.focus(); }, 30); };
  var closeOverlay = function (ov) { ov.classList.remove('active'); ov.hidden = true; };

  var lead = $('#leadOverlay');
  if (lead) {
    var lf = $('#leadForm'), le = $('#leadError'), timer, shown = false, KEY = 'dsaLead';
    var showLead = function (force) { if (typeof reset === 'function') reset(); if (!force && (shown || $('#popupOverlay.active'))) return; shown = true; openOverlay(lead); };
    var hideLead = function (days) { closeOverlay(lead); clearTimeout(timer); var d = $('#leadDontShow').checked ? 3650 : (days || 3); storePut(KEY, { until: Date.now() + d * DAY }); };
    if (lead.dataset.auto === '1' && !((storeGet(KEY).until || 0) > Date.now())) {
      timer = setTimeout(showLead, 9000);
      window.addEventListener('scroll', function onS() { if (window.scrollY > window.innerHeight * 0.8) { window.removeEventListener('scroll', onS); clearTimeout(timer); timer = setTimeout(showLead, 1500); } }, { passive: true });
    }
    document.addEventListener('click', function (e) { var b = e.target.closest && e.target.closest('[data-open-lead]'); if (b) { e.preventDefault(); clearTimeout(timer); showLead(true); } });
    lead.addEventListener('click', function (e) { if (e.target === lead) hideLead(); });
    Array.prototype.forEach.call(lead.querySelectorAll('[data-lead-close]'), function (b) { b.addEventListener('click', function () { hideLead(); }); });
    var more = $('#leadMore'), rb = $('#leadRefine');
    if (rb) rb.addEventListener('click', function () { more.hidden = !more.hidden; rb.setAttribute('aria-expanded', String(!more.hidden)); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && lead.classList.contains('active')) hideLead(); });
    var bad = function (el, m) { le.textContent = m; le.hidden = false; el.focus(); };
    var reset = function () { lf.hidden = false; var d = $('#leadDone'); if (d) d.hidden = true; };
    lf.addEventListener('submit', function (e) {
      e.preventDefault(); le.hidden = true;
      var f = lf.elements, name = f.name.value.trim(), email = f.email.value.trim(), wa = f.whatsapp.value.trim();
      if (name.length < 2) return bad(f.name, 'Please enter your name.');
      if (!email && !wa) return bad(f.email, 'Please enter your email or WhatsApp number.');
      if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return bad(f.email, 'Please enter a valid email address.');
      if (wa && !/^\+?[0-9 ()\-.]{7,22}$/.test(wa)) return bad(f.whatsapp, 'Please enter a valid WhatsApp number.');
      var btn = $('button[type=submit]', lf); btn.disabled = true;
      var body = new URLSearchParams(new FormData(lf)); body.set('page', location.pathname); body.set('lang', document.documentElement.lang || '');
      fetch(lf.action, { method: 'POST', body: body, credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (r) {
          btn.disabled = false;
          if (r.ok && r.j.success) { lf.hidden = true; var d = $('#leadDone'); if (d) d.hidden = false; storePut(KEY, { until: Date.now() + 30 * DAY }); }
          else if (r.j && r.j.error === 'phone') bad(f.whatsapp, 'Please enter a valid phone number.');
          else if (r.j && r.j.error === 'name') bad(f.name, 'Please enter your name.');
          else { le.textContent = 'Something went wrong. Please try again in a moment.'; le.hidden = false; }
        })
        .catch(function () { btn.disabled = false; le.textContent = 'Network problem. Please try again.'; le.hidden = false; });
    });
  }

  var ad = $('#popupOverlay');
  if (ad) {
    var reloaded = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0] || {}).type === 'reload';
    if (reloaded && !((storeGet('dsaAd').until || 0) > Date.now())) openOverlay(ad);
    var hideAd = function () { closeOverlay(ad); if ($('#dontShowAgain').checked) storePut('dsaAd', { until: Date.now() + 3650 * DAY }); };
    $('[data-ad-close]', ad).addEventListener('click', hideAd);
    ad.addEventListener('click', function (e) { if (e.target === ad) hideAd(); });
  }

  // Gallery lightbox (any link with data-lightbox)
  var lbLinks = $$('a[data-lightbox]');
  if (lbLinks.length) {
    var lb = document.createElement('div'); lb.className = 'modal-overlay lightbox'; lb.hidden = true;
    lb.innerHTML = '<button type="button" class="modal-close" aria-label="Close">&times;</button><button type="button" class="lb-prev" aria-label="Previous">&#8249;</button><figure><img alt=""><figcaption></figcaption></figure><button type="button" class="lb-next" aria-label="Next">&#8250;</button>';
    document.body.appendChild(lb);
    var idx = 0, img = $('img', lb), cap = $('figcaption', lb);
    var show = function (i) { idx = (i + lbLinks.length) % lbLinks.length; img.src = lbLinks[idx].href; cap.textContent = lbLinks[idx].dataset.title || ''; lb.hidden = false; lb.classList.add('active'); };
    lbLinks.forEach(function (a, i) { a.addEventListener('click', function (e) { e.preventDefault(); show(i); }); });
    var close = function () { lb.classList.remove('active'); lb.hidden = true; img.removeAttribute('src'); };
    $('.modal-close', lb).addEventListener('click', close);
    $('.lb-prev', lb).addEventListener('click', function () { show(idx - 1); });
    $('.lb-next', lb).addEventListener('click', function () { show(idx + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) { if (lb.hidden) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') show(idx - 1); if (e.key === 'ArrowRight') show(idx + 1); });
  }

  // Simple tabs / slider helpers
  $$('[data-tabs]').forEach(function (box) {
    var tabs = $$('[data-tab]', box), panes = $$('[data-pane]', box);
    tabs.forEach(function (t) { t.addEventListener('click', function () {
      tabs.forEach(function (x) { x.classList.toggle('selected', x === t); x.setAttribute('aria-pressed', x === t); });
      panes.forEach(function (p) { p.hidden = p.dataset.pane !== t.dataset.tab; });
    }); });
  });
  $$('[data-slider]').forEach(function (box) {
    var slides = $$('[data-slide]', box), caps = $$('[data-cap]', box), i = 0;
    var saver = (navigator.connection && navigator.connection.saveData) || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
    var play = function (n) {
      $$('video', box).forEach(function (v) { if (slides[n].contains(v)) { if (!saver) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } } else v.pause(); });
    };
    var go = function (n) {
      slides[i].classList.remove('on'); if (caps[i]) caps[i].classList.remove('on');
      i = n; slides[i].classList.add('on'); if (caps[i]) caps[i].classList.add('on'); play(i);
    };
    window.addEventListener('load', function () { play(0); });
    if (slides.length > 1) setInterval(function () { go((i + 1) % slides.length); }, 7000);
  });
  // Trip filter bar (/safaris)
  var filters = $$('.trip-filters button');
  if (filters.length) {
    var match = {
      'All journeys': function () { return true; },
      'Kenya': function (c) { return c.dataset.region.indexOf('Kenya') > -1; },
      'Tanzania': function (c) { return c.dataset.region.indexOf('Tanzania') > -1; },
      'Uganda': function (c) { return c.dataset.region === 'Uganda'; },
      'Trek & coast': function (c) { return c.dataset.dest === 'kilimanjaro' || c.dataset.dest === 'beach'; }
    };
    filters.forEach(function (b) {
      b.addEventListener('click', function () {
        filters.forEach(function (o) { var on = o === b; o.classList.toggle('selected', on); o.setAttribute('aria-pressed', on); });
        var shown = 0;
        $$('.trip-card').forEach(function (c) { var ok = match[b.dataset.filter](c); c.hidden = !ok; if (ok) shown++; });
        $('#empty-trips').hidden = shown > 0;
      });
    });
  }

  // Enquiry form
  var card = $('#enquire'), form = $('#lead-form');
  if (card && form) {
    var questions = JSON.parse(($('#questions-data') || { textContent: '{}' }).textContent);
    var dest = $('#destination'), busy = false;
    var tripId = $('#trip-id'), tripBox = $('#selected-trip');
    var q = [0, 1].map(function (i) { return { wrap: $('#q' + i + '-wrap'), label: $('#q' + i + '-label'), select: $('#q' + i) }; });

    var fillQuestions = function (key) {
      var list = (key && questions[key]) || [];
      q.forEach(function (slot, i) {
        var item = list[i];
        slot.wrap.hidden = !item;
        if (!item) { slot.select.innerHTML = ''; slot.select.name = ''; return; }
        slot.label.textContent = item.label;
        slot.select.name = 'answer__' + item.key;
        slot.select.innerHTML = '';
        [['', 'Choose an option']].concat(item.options.map(function (o) { return [o, o]; })).forEach(function (o) {
          var el = document.createElement('option'); el.value = o[0]; el.textContent = o[1]; slot.select.appendChild(el);
        });
      });
    };
    if (dest && dest.tagName === 'SELECT') {
      dest.addEventListener('change', function () { fillQuestions(dest.value); tripId.value = ''; tripBox.hidden = true; });
    }
    $('#clear-trip').addEventListener('click', function () { tripId.value = ''; tripBox.hidden = true; });

    var refine = $('#refine'), refinement = $('#refinement');
    refine.addEventListener('click', function () {
      var open = refinement.hidden;
      refinement.hidden = !open;
      refine.setAttribute('aria-expanded', open);
      refine.lastElementChild.classList.toggle('rotate', open);
    });

    var showError = function (msg, ref) {
      $('#form-error-text').textContent = msg;
      var r = $('#form-error-ref');
      r.hidden = !ref; r.textContent = ref ? 'Reference: ' + ref.slice(0, 8).toUpperCase() : '';
      $('#form-error').hidden = false;
    };
    var setBusy = function (on) {
      busy = on;
      $('#submit-btn').disabled = on;
      $('.idle', form).hidden = on;
      $('.busy', form).hidden = !on;
    };

    form.addEventListener('submit', function (e) {
      if (!window.fetch || !window.FormData) return; // falls back to a normal form post
      e.preventDefault();
      if (busy) return;
      var data = new FormData(form), body = {}, answers = {}, utm = {};
      data.forEach(function (v, k) { if (k.indexOf('answer__') === 0) { if (v) answers[k.slice(8)] = v; } else body[k] = v; });
      body.answers = answers;
      body.travellers = Number(body.travellers);
      var params = new URLSearchParams(location.search);
      ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) { if (params.get(k)) utm[k] = params.get(k); });
      body.utm = utm;
      delete body.csrfmiddlewaretoken;
      $('#form-error').hidden = true;
      setBusy(true);
      fetch(form.action, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': data.get('csrfmiddlewaretoken') },
        body: JSON.stringify(body)
      }).then(function (res) { return res.json().catch(function () { return {}; }).then(function (j) { return { ok: res.ok, j: j }; }); })
        .then(function (r) {
          if (!r.ok || !r.j.success) throw { message: r.j.error, ref: r.j.reference };
          var label = dest ? (dest.tagName === 'SELECT' ? dest.options[dest.selectedIndex].text : $('#form-title').textContent) : 'trip';
          $('#success-label').textContent = (dest && dest.tagName === 'SELECT' && !dest.value ? 'East Africa adventure' : label).toLowerCase();
          $('#success-ref').textContent = r.j.reference.slice(0, 8).toUpperCase();
          $('.form-view', card).hidden = true;
          $('.success-view', card).hidden = false;
          card.classList.add('success-card');
          card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        })
        .catch(function (err) { setBusy(false); showError((err && err.message) || 'Please try again or contact us on WhatsApp.', err && err.ref); });
    });
  }

  // Google reviews (loaded when scrolled near)
  var rv = $('#traveller-reviews');
  if (rv) {
    var NS = 'http://www.w3.org/2000/svg';
    var star = function (cls) {
      var s = document.createElementNS(NS, 'svg'); s.setAttribute('width', 15); s.setAttribute('height', 15); s.setAttribute('viewBox', '0 0 24 24');
      s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor'); s.setAttribute('stroke-width', 2); s.setAttribute('aria-hidden', 'true');
      if (cls) s.setAttribute('class', cls);
      var p = document.createElementNS(NS, 'path');
      p.setAttribute('d', 'M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z');
      s.appendChild(p); return s;
    };
    var el = function (tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
    var stars = function (rating) {
      var w = el('span', 'review-stars'); w.setAttribute('role', 'img'); w.setAttribute('aria-label', rating + ' out of 5 stars');
      for (var n = 1; n <= 5; n++) {
        var c = el('span'); c.appendChild(star('star-base'));
        var f = el('span', 'star-fill'); f.style.width = Math.max(0, Math.min(1, rating - n + 1)) * 100 + '%'; f.appendChild(star());
        c.appendChild(f); w.appendChild(c);
      }
      return w;
    };
    var link = function (href, cls) { var a = el('a', cls); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; };
    var card_ = function (r) {
      var art = el('article', 'google-review-card');
      var who = r.authorUrl ? link(r.authorUrl, 'review-author') : el('div', 'review-author');
      if (r.avatar) { var im = el('img'); im.src = r.avatar; im.alt = ''; im.width = im.height = 42; im.loading = 'lazy'; im.referrerPolicy = 'no-referrer'; who.appendChild(im); }
      else who.appendChild(el('span', 'review-avatar', r.author.slice(0, 1)));
      var nm = el('span'); nm.appendChild(el('strong', '', r.author)); if (r.date) nm.appendChild(el('small', '', r.date)); who.appendChild(nm);
      art.appendChild(who);
      if (r.rating !== null) art.appendChild(stars(r.rating));
      if (r.text) {
        var p = el('p', 'review-text', r.text); art.appendChild(p);
        if (r.text.length > 240) {
          var b = el('button', 'review-expand', 'Read more'); b.type = 'button'; b.setAttribute('aria-expanded', 'false');
          b.addEventListener('click', function () { var on = p.classList.toggle('expanded'); b.textContent = on ? 'Show less' : 'Read more'; b.setAttribute('aria-expanded', on); });
          art.appendChild(b);
        }
      } else art.appendChild(el('p', 'review-empty-comment', 'This review has no written comment.'));
      if (r.translated) art.appendChild(el('small', 'review-translation', 'Translated by Google. View the original on Google Maps.'));
      var s = link(r.sourceUrl, 'review-source'); s.appendChild(document.createTextNode('View review on Google Maps ↗')); art.appendChild(s);
      return art;
    };
    var started = false;
    var load = function () {
      if (started) return; started = true;
      $('#rv-title').textContent = 'Loading traveller reviews…';
      $('#rv-text').textContent = 'Connecting to Google Maps.';
      fetch(rv.dataset.endpoint, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
        if (d.status !== 'live' || !Array.isArray(d.reviews)) throw 0;
        $('#rv-name').textContent = d.name;
        if (d.rating !== null) {
          var sc = $('#rv-score'); sc.hidden = false; $('#rv-label').hidden = true;
          sc.appendChild(el('strong', '', d.rating.toFixed(1)));
          var box = el('div'); box.appendChild(stars(d.rating));
          if (d.count !== null) box.appendChild(el('span', '', d.count.toLocaleString() + ' Google ' + (d.count === 1 ? 'review' : 'reviews')));
          sc.appendChild(box);
        }
        if (d.reviews.length) {
          var g = $('#rv-grid'); d.reviews.forEach(function (r) { g.appendChild(card_(r)); });
          g.hidden = false; $('#rv-order').hidden = false; $('#rv-fallback').hidden = true;
        } else { $('#rv-title').textContent = 'Meet us through our travellers.'; $('#rv-text').textContent = 'Read traveller ratings and experiences on our Google Maps listing.'; }
        d.attributions.forEach(function (a) {
          var p = el('p', 'review-provider');
          if (a.url) { var l = link(a.url); l.textContent = a.name; p.appendChild(l); } else p.textContent = a.name;
          $('#rv-attr').appendChild(p);
        });
      }).catch(function () {
        $('#rv-title').textContent = 'Meet us through our travellers.';
        $('#rv-text').textContent = 'Reviews are available on our Google Maps listing. The on-site review feed is currently unavailable.';
      });
    };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es) { if (es.some(function (x) { return x.isIntersecting; })) { io.disconnect(); load(); } }, { rootMargin: '300px' });
      io.observe(rv);
    } else load();
  }
})();
