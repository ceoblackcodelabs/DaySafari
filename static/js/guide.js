(function () {
  'use strict';
  var root = document.getElementById('guideRoot'); if (!root) return;
  var $ = function (s, r) { return (r || document).querySelector(s); }, $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var csrf = ($('meta[name=csrf-token]') || {}).content || '';
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  var cp = $('#copyPhone');
  if (cp) cp.addEventListener('click', function () { (navigator.clipboard ? navigator.clipboard.writeText(cp.dataset.copy) : Promise.reject()).then(function () { cp.textContent = 'Copied'; }, function () { prompt('Copy', cp.dataset.copy); }); });

  // Lead form
  $$('form[data-lead]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      $$('.ferr', form).forEach(function (e) { e.textContent = ''; });
      var btn = $('button[type=submit]', form); btn.disabled = true;
      fetch(form.dataset.url, { method: 'POST', body: new FormData(form), headers: { 'X-CSRFToken': csrf }, credentials: 'same-origin' })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (x) {
          btn.disabled = false;
          if (x.ok && x.j.ok) {
            $('.fields', form).hidden = true; $('.done', form).hidden = false;

            form.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
          } else {
            var er = x.j.errors || {};
            Object.keys(er).forEach(function (k) { var m = $('.ferr[data-for=' + k + ']', form); if (m) m.textContent = er[k]; });
            if (!x.j.errors) alert(x.j.error || 'Something went wrong. Please try again.');
          }
        }).catch(function () { btn.disabled = false; alert('Network problem. Please try again.'); });
    });
  });

  // QR code (library loads only when the card is near the screen)
  var qrCard = $('#qrCard'), qrBox = $('#qrBox'), qrLoaded = false, qrSvg = '';
  function qrUrl() { var u = new URL(qrCard.dataset.url); var ev = ($('#eventPick') || {}).value || ''; u.searchParams.set('src', ev ? 'event' : 'qr'); if (ev) u.searchParams.set('event', ev); return u.toString(); }
  function drawQr() { if (!window.qrcode) return; var q = qrcode(0, 'M'); q.addData(qrUrl()); q.make(); qrSvg = q.createSvgTag({ cellSize: 6, margin: 2, scalable: true }); qrBox.innerHTML = qrSvg; qrBox.firstChild.style.width = '100%'; }
  function loadQr() { if (qrLoaded) return; qrLoaded = true; var s = document.createElement('script'); s.src = '/static/js/qrcode.min.js'; s.onload = drawQr; s.onerror = function () { qrBox.textContent = 'Open the link instead'; }; document.head.appendChild(s); }
  if (qrCard) {
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es, o) { if (es[0].isIntersecting) { loadQr(); o.disconnect(); } }, { rootMargin: '400px' }).observe(qrCard); else loadQr();
    var evp = $('#eventPick'); if (evp) evp.addEventListener('change', function () { if (window.qrcode) drawQr(); });
    $('#copyLink').addEventListener('click', function () { var u = qrUrl(); (navigator.clipboard ? navigator.clipboard.writeText(u) : Promise.reject()).then(function () { $('#copyLink').textContent = 'Copied'; }, function () { prompt('Copy this link', u); }); });
    $('#shareLink').addEventListener('click', function () { var u = qrUrl(); if (navigator.share) navigator.share({ title: document.title, url: u }).catch(function () {}); else prompt('Copy this link', u); });
    $('#dlQr').addEventListener('click', function () {
      if (!qrSvg) { loadQr(); return; }
      var img = new Image(), b = new Blob([qrSvg], { type: 'image/svg+xml' }), url = URL.createObjectURL(b);
      img.onload = function () { var c = document.createElement('canvas'); c.width = c.height = 640; var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, 640, 640); x.drawImage(img, 0, 0, 640, 640); var a = document.createElement('a'); a.download = root.dataset.slug + '-qr.png'; a.href = c.toDataURL('image/png'); a.click(); URL.revokeObjectURL(url); };
      img.src = url;
    });
  }

  // Inline editing (managers only)
  var tog = $('#editToggle'); if (!tog) return;
  var msg = $('#edMsg'), original = {};
  var fields = function () { return $$('[data-edit]'); };
  function setEditing(on) {
    document.body.classList.toggle('editing', on);
    fields().forEach(function (el) { el.contentEditable = on ? 'true' : 'false'; if (on) original[el.dataset.edit] = el.innerHTML; });
    if (on) { $('#about').scrollIntoView({ behavior: 'smooth' }); msg.textContent = ''; }
  }
  tog.addEventListener('click', function () { setEditing(!document.body.classList.contains('editing')); });
  $('#edCancel').addEventListener('click', function () { fields().forEach(function (el) { if (original[el.dataset.edit] !== undefined) el.innerHTML = original[el.dataset.edit]; }); setEditing(false); });
  fields().forEach(function (el) {
    if (!el.dataset.rich) el.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); el.blur(); } });
    el.addEventListener('paste', function (e) { e.preventDefault(); var t = (e.clipboardData || window.clipboardData).getData('text/plain'); document.execCommand('insertText', false, t); });
  });
  $$('.rich-tools button').forEach(function (b) { b.addEventListener('mousedown', function (e) { e.preventDefault(); document.execCommand(b.dataset.cmd, false, null); }); });
  $('#edSave').addEventListener('click', function () {
    var body = {};
    fields().forEach(function (el) { body[el.dataset.edit] = el.dataset.rich ? el.innerHTML : el.textContent; });
    $$('[data-field]').forEach(function (el) { body[el.dataset.field] = el.value; });
    msg.textContent = 'Saving...';
    fetch(root.dataset.editUrl, { method: 'POST', headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify(body) })
      .then(function (r) { return r.json(); }).then(function (j) { if (j.ok) { msg.textContent = 'Saved. Refreshing...'; setTimeout(function () { location.reload(); }, 500); } else msg.textContent = j.error || 'Could not save'; })
      .catch(function () { msg.textContent = 'Network problem'; });
  });

  // Photo cropper: pick or re-crop, drag + zoom, send a 4:5 JPEG
  var cm = $('#cropModal'), cf = $('#cFrame'), ci = $('#cImg'), cz = $('#cZoom'), W = 0, H = 0, base = 1, sc = 1, ox = 0, oy = 0, drag = null;
  function clamp() { var fw = cf.clientWidth, fh = cf.clientHeight, w = W * sc, h = H * sc; ox = Math.min(0, Math.max(fw - w, ox)); oy = Math.min(0, Math.max(fh - h, oy)); }
  function paint() { clamp(); ci.style.transform = 'translate(' + ox + 'px,' + oy + 'px) scale(' + sc + ')'; }
  function openCrop(src) {
    cm.hidden = false; cm.classList.add('active');
    ci.onload = function () { W = ci.naturalWidth; H = ci.naturalHeight; var fw = cf.clientWidth, fh = cf.clientHeight; base = Math.max(fw / W, fh / H); cz.value = 1; sc = base; ox = (fw - W * sc) / 2; oy = (fh - H * sc) / 2; paint(); };
    ci.src = src;
  }
  function closeCrop() { cm.classList.remove('active'); cm.hidden = true; }
  cz.addEventListener('input', function () { var fw = cf.clientWidth, fh = cf.clientHeight, cx = (fw / 2 - ox) / sc, cy = (fh / 2 - oy) / sc; sc = base * cz.value; ox = fw / 2 - cx * sc; oy = fh / 2 - cy * sc; paint(); });
  cf.addEventListener('pointerdown', function (e) { drag = { x: e.clientX - ox, y: e.clientY - oy }; cf.setPointerCapture(e.pointerId); });
  cf.addEventListener('pointermove', function (e) { if (!drag) return; ox = e.clientX - drag.x; oy = e.clientY - drag.y; paint(); });
  ['pointerup', 'pointercancel'].forEach(function (ev) { cf.addEventListener(ev, function () { drag = null; }); });
  $('#cCancel').addEventListener('click', closeCrop);
  $('#photoFile').addEventListener('change', function () { var f = this.files[0]; this.value = ''; if (!f) return; var r = new FileReader(); r.onload = function () { openCrop(r.result); }; r.readAsDataURL(f); });
  var rc = $('#recrop'); if (rc) rc.addEventListener('click', function () { openCrop(root.dataset.photoSrc); });
  $('#cSave').addEventListener('click', function () {
    var fw = cf.clientWidth, fh = cf.clientHeight, k = 900 / fw, c = document.createElement('canvas'); c.width = 900; c.height = Math.round(fh * k);
    var x = c.getContext('2d'); x.imageSmoothingQuality = 'high'; x.drawImage(ci, -ox / sc, -oy / sc, fw / sc, fh / sc, 0, 0, c.width, c.height);
    c.toBlob(function (blob) {
      var fd = new FormData(); fd.append('photo', blob, 'photo.jpg'); msg.textContent = 'Uploading photo...'; closeCrop();
      fetch(root.dataset.photoUrl, { method: 'POST', body: fd, headers: { 'X-CSRFToken': csrf }, credentials: 'same-origin' })
        .then(function (r) { return r.json(); }).then(function (j) { if (j.ok) { $('#photoBox').innerHTML = '<img id="photoImg" src="' + j.url + '?' + Date.now() + '" alt="">'; msg.textContent = 'Photo updated'; } else msg.textContent = j.error || 'Upload failed'; })
        .catch(function () { msg.textContent = 'Network problem'; });
    }, 'image/jpeg', 0.9);
  });
  if (location.hash === '#edit') setEditing(true);
})();
