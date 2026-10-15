/* Pipeline Products Online: sample homepage concept.
   No network requests, no storage, no submission. All state lives in memory for this page view. */
(function () {
  'use strict';

  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
  var wait = function (ms) { return reduceMotion.matches ? 0 : ms; };

  // Reveal JS-only controls
  $$('[data-js-only]').forEach(function (el) { el.hidden = false; });

  /* ---------------- Images: labelled placeholder when blocked ---------------- */
  function showFallback(img) {
    var frame = img.closest('.frame');
    if (!frame || frame.classList.contains('is-missing')) return;
    frame.classList.add('is-missing');
    img.hidden = true;
    var box = document.createElement('div');
    box.className = 'img-fallback';
    box.setAttribute('role', 'img');
    box.setAttribute('aria-label', 'Image not loaded: ' + img.alt);
    box.innerHTML = '<strong>Image not loaded</strong><span>' + img.getAttribute('data-fallback') +
      ' from pipelineproductsonline.com. Placeholder shown; confirm image access and rights.</span>';
    frame.appendChild(box);
  }
  $$('img[data-fallback]').forEach(function (img) {
    img.addEventListener('error', function () { showFallback(img); });
    if (img.complete && img.naturalWidth === 0 && img.currentSrc) showFallback(img);
  });

  /* ---------------- Header: scrolled state, mobile menu ---------------- */
  var header = $('.site-header');
  var nav = $('#primary-nav');
  var toggle = $('.menu-toggle');
  var mobileMq = window.matchMedia('(max-width: 940px)');

  function setMenu(open, opts) {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    $('.menu-toggle__label', toggle).textContent = open ? 'Close' : 'Menu';
    if (!open && opts && opts.returnFocus) toggle.focus();
    if (open) { var first = $('a', nav); if (first) first.focus({ preventScroll: true }); }
  }
  toggle.addEventListener('click', function () {
    setMenu(toggle.getAttribute('aria-expanded') !== 'true');
  });
  nav.addEventListener('click', function (e) {
    if (e.target.closest('a') && mobileMq.matches) setMenu(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setMenu(false, { returnFocus: true });
  });
  document.addEventListener('click', function (e) {
    if (toggle.getAttribute('aria-expanded') === 'true' && !e.target.closest('.site-header')) setMenu(false);
  });
  mobileMq.addEventListener('change', function () { setMenu(false); });

  // Keep the sticky offset accurate whatever the header height is
  function syncHeaderHeight() { root.style.setProperty('--header-h', header.offsetHeight + 'px'); }
  syncHeaderHeight();
  window.addEventListener('resize', syncHeaderHeight);

  /* ---------------- Active section + back to top ---------------- */
  var navLinks = $$('a', nav);
  var sections = navLinks.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  var toTop = $('#to-top');
  var hero = $('.hero');
  toTop.hidden = false;

  var ticking = false;
  function onScroll() {
    ticking = false;
    var y = window.scrollY;
    header.classList.toggle('is-scrolled', y > 8);
    toTop.classList.toggle('is-visible', y > hero.offsetTop + hero.offsetHeight);
    toTop.tabIndex = toTop.classList.contains('is-visible') ? 0 : -1;
    toTop.setAttribute('aria-hidden', toTop.classList.contains('is-visible') ? 'false' : 'true');

    var line = header.offsetHeight + window.innerHeight * 0.3;
    var current = null;
    sections.forEach(function (s, i) {
      if (s && s.getBoundingClientRect().top <= line) current = i;
    });
    if (window.innerHeight + y >= document.documentElement.scrollHeight - 4) current = sections.length - 1;
    if (current !== null && sections[current].getBoundingClientRect().bottom < header.offsetHeight) current = null;
    navLinks.forEach(function (a, i) {
      var on = i === current;
      a.classList.toggle('is-active', on);
      if (on) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
    });
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: reduceMotion.matches ? 'auto' : 'smooth' });
    $('.wordmark').focus({ preventScroll: true });
  });

  /* ---------------- Reveals (one quiet entrance per block) ---------------- */
  if ('IntersectionObserver' in window && !reduceMotion.matches) {
    var revealTargets = [];
    $$('.section-head, .featured__figure, .featured__body, .brand-grid, .materials__chips, .lines-more').forEach(function (el) { revealTargets.push(el); });
    $$('.range-card').forEach(function (el, i) { el.style.setProperty('--i', i % 6); revealTargets.push(el); });
    $$('.line-card').forEach(function (el, i) { el.style.setProperty('--i', i); revealTargets.push(el); });
    revealTargets.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.92) return; // already in view: never hide
      el.classList.add('reveal');
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    $$('.reveal').forEach(function (el) { io.observe(el); });
  }
  requestAnimationFrame(function () { requestAnimationFrame(function () { root.classList.add('is-loaded'); }); });

  /* ---------------- Range filter ---------------- */
  var chipsWrap = $('.filter__chips');
  var chips = $$('.chip', chipsWrap);
  var indicator = $('.filter__indicator');
  var cards = $$('.range-card');
  var countEl = $('#range-count');
  var labels = { all: 'all types', y: 'Y strainers', basket: 'basket and simplex strainers', duplex: 'duplex strainers', automatic: 'automatic strainers and accessories' };
  var currentFilter = 'all';
  var filterTimer = null;

  function placeIndicator(chip, instant) {
    if (!chip) return;
    var wr = chipsWrap.getBoundingClientRect(), r = chip.getBoundingClientRect();
    if (instant) indicator.style.transition = 'none';
    indicator.style.setProperty('--ind-x', (r.left - wr.left - chipsWrap.clientLeft) + 'px');
    indicator.style.setProperty('--ind-y', (r.top - wr.top - chipsWrap.clientTop) + 'px');
    indicator.style.setProperty('--ind-w', r.width + 'px');
    indicator.style.setProperty('--ind-h', r.height + 'px');
    if (instant) { void indicator.offsetWidth; indicator.style.transition = ''; }
  }
  function activeChip() { return chips.filter(function (ch) { return ch.getAttribute('aria-pressed') === 'true'; })[0]; }

  function applyFilter(type, opts) {
    currentFilter = type;
    chips.forEach(function (ch) { ch.setAttribute('aria-pressed', String(ch.dataset.filter === type)); });
    var active = chips.filter(function (ch) { return ch.dataset.filter === type; })[0];
    placeIndicator(active, opts && opts.instant);

    var show = cards.filter(function (c) { return type === 'all' || c.dataset.type === type; });
    var hide = cards.filter(function (c) { return show.indexOf(c) === -1; });
    clearTimeout(filterTimer);

    hide.forEach(function (c) { if (!c.hidden) c.classList.add('is-leaving'); });
    filterTimer = setTimeout(function () {
      hide.forEach(function (c) { c.hidden = true; c.classList.remove('is-leaving', 'is-entering'); });
      show.forEach(function (c, i) {
        var wasHidden = c.hidden;
        c.hidden = false;
        c.classList.remove('is-leaving');
        if (wasHidden && !reduceMotion.matches) {
          c.classList.remove('is-entering'); void c.offsetWidth;
          c.style.setProperty('--i', i);
          c.classList.add('is-entering');
        }
      });
    }, wait(hide.length ? 170 : 0));

    countEl.textContent = type === 'all'
      ? 'Showing all ' + show.length + ' listings'
      : 'Showing ' + show.length + ' of ' + cards.length + ' listings: ' + labels[type];
  }

  chips.forEach(function (ch) {
    ch.addEventListener('click', function () { applyFilter(ch.dataset.filter); });
  });
  cards.forEach(function (c) { c.addEventListener('animationend', function (e) {
    c.classList.remove('is-entering');
    if (e.animationName === 'flash' && !reduceMotion.matches) c.classList.remove('is-flash');
  }); });

  chipsWrap.classList.add('has-indicator');
  applyFilter('all', { instant: true });
  window.addEventListener('resize', function () { placeIndicator(activeChip(), true); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { placeIndicator(activeChip(), true); });

  // Type index links in the hero preset the filter
  $$('[data-jump-filter]').forEach(function (a) {
    a.addEventListener('click', function () { applyFilter(a.dataset.jumpFilter); });
  });

  /* ---------------- Materials: which listings mention each material ---------------- */
  var materialMap = {
    'carbon-steel': ['item-y-cs-ss', 'item-b-cs-di'],
    'stainless': ['item-y-cs-ss', 'item-b-316', 'item-d-50'],
    'ductile': ['item-y-di', 'item-b-cs-di'],
    'cast-iron': ['item-y-ci', 'item-d-ci-br'],
    'bronze': ['item-y-br', 'item-b-bronze', 'item-d-ci-br'],
    'al-bronze': ['item-y-ab']
  };
  var mchips = $$('.mchip');
  var mOut = $('#materials-out');

  function flashCard(card) {
    if (card.hidden) applyFilter('all');
    setTimeout(function () {
      card.scrollIntoView({ behavior: reduceMotion.matches ? 'auto' : 'smooth', block: 'center' });
      card.classList.remove('is-flash'); void card.offsetWidth; card.classList.add('is-flash');
      if (reduceMotion.matches) setTimeout(function () { card.classList.remove('is-flash'); }, 2000);
      var btn = $('.btn--add', card);
      btn.focus({ preventScroll: true });
    }, wait(card.hidden ? 200 : 0));
  }

  mchips.forEach(function (mc) {
    mc.addEventListener('click', function () {
      var on = mc.getAttribute('aria-pressed') !== 'true';
      mchips.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
      mOut.innerHTML = '';
      if (!on) return;
      mc.setAttribute('aria-pressed', 'true');
      var ids = materialMap[mc.dataset.material] || [];
      var wrap = document.createElement('div');
      wrap.className = 'materials__result';
      var p = document.createElement('p');
      p.textContent = mc.textContent + ' appears in ' + ids.length + (ids.length === 1 ? ' listing' : ' listings') +
        ' in the range preview. Check with the team before choosing a material for your service.';
      var ul = document.createElement('ul');
      ids.forEach(function (id) {
        var card = document.getElementById(id);
        var li = document.createElement('li');
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'materials__jump';
        b.textContent = $('.range-card__title', card).textContent;
        b.setAttribute('aria-label', 'Show listing: ' + b.textContent);
        b.addEventListener('click', function () { flashCard(card); });
        li.appendChild(b); ul.appendChild(li);
      });
      wrap.appendChild(p); wrap.appendChild(ul);
      mOut.appendChild(wrap);
    });
  });


  /* ---------------- Kraissl details disclosure ---------------- */
  var dToggle = $('#kraissl-details-toggle');
  var dPanel = $('#kraissl-details');
  dPanel.hidden = true;
  dPanel.setAttribute('role', 'region');
  dPanel.setAttribute('aria-labelledby', 'kraissl-details-toggle');
  var dTimer = null;
  dToggle.addEventListener('click', function () {
    var open = dToggle.getAttribute('aria-expanded') !== 'true';
    dToggle.setAttribute('aria-expanded', String(open));
    $('[data-label-closed]', dToggle).hidden = open;
    $('[data-label-open]', dToggle).hidden = !open;
    clearTimeout(dTimer);
    if (open) {
      dPanel.hidden = false;
      void dPanel.offsetHeight;
      dPanel.dataset.open = 'true';
    } else {
      dPanel.dataset.open = 'false';
      dTimer = setTimeout(function () { dPanel.hidden = true; }, wait(360));
    }
  });

  /* ---------------- Toast ---------------- */
  var toast = $('#toast');
  var toastTimer = null;
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('is-visible'); }, 2600);
  }

  /* ---------------- Request sheet ---------------- */
  var PRESSURE = ['Not sure', 'Class 125', 'Class 150', 'Class 300', 'Class 600', 'PN 10', 'PN 16', 'PN 25', 'PN 40', 'Other (see notes)'];
  var MATERIALS = ['Not sure', 'Carbon steel (WCB)', 'Stainless steel / 316SS', 'Ductile iron', 'Cast iron', 'Bronze / brass', 'Aluminum bronze', 'Cast steel', 'Other (see notes)'];
  var UNITS = [['in', 'inch'], ['mm', 'mm'], ['DN', 'DN']];

  var lines = [];   // { id, name, custom, size, unit, pressure, material, qty, notes, source }
  var seq = 0;
  var linesEl = $('#sheet-lines');
  var emptyEl = $('#sheet-empty');
  var form = $('#quote-form');
  var reviewEl = $('#review');
  var countBadges = $$('[data-quote-num]');
  var lineCountEl = $('[data-line-count]');

  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function options(list, sel) { return list.map(function (o) { var v = Array.isArray(o) ? o[0] : o; var t = Array.isArray(o) ? o[1] : o; return '<option value="' + esc(v) + '"' + (v === sel ? ' selected' : '') + '>' + esc(t) + '</option>'; }).join(''); }

  function updateCounts(bump) {
    var n = lines.length;
    countBadges.forEach(function (b) { b.textContent = n; });
    $$('[data-quote-count]').forEach(function (b) {
      if (bump && !reduceMotion.matches) { b.classList.remove('is-bumped'); void b.offsetWidth; b.classList.add('is-bumped'); }
    });
    lineCountEl.textContent = n + (n === 1 ? ' line' : ' lines');
    emptyEl.hidden = n > 0;
    $$('.line', linesEl).forEach(function (li, i) { $('.line__num', li).textContent = i + 1; });
  }

  function lineHTML(l) {
    var p = 'l' + l.id;
    var nameBlock = l.custom
      ? '<div class="field" style="flex:1"><label for="' + p + '-name">Item <span class="req" aria-hidden="true">*</span></label>' +
        '<input id="' + p + '-name" data-k="name" type="text" value="' + esc(l.name) + '" placeholder="For example: gate valve, flanged" aria-describedby="' + p + '-name-err">' +
        '<p class="field__err" id="' + p + '-name-err"></p></div>'
      : '<p class="line__name" id="' + p + '-title">' + esc(l.name) + '</p>';
    return '' +
      '<div class="line__num" aria-hidden="true"></div>' +
      '<div class="line__body">' +
        '<div class="line__head">' + nameBlock +
          '<button type="button" class="line__remove" data-remove="' + l.id + '" aria-label="Remove ' + esc(l.name || 'this line') + '">Remove</button>' +
        '</div>' +
        '<div class="line__fields">' +
          '<div class="field"><label for="' + p + '-size">Pipe size</label>' +
            '<div class="combo"><input id="' + p + '-size" data-k="size" type="text" inputmode="decimal" value="' + esc(l.size) + '" placeholder="For example: 2" autocomplete="off">' +
            '<select id="' + p + '-unit" data-k="unit" aria-label="Size unit">' + options(UNITS, l.unit) + '</select></div></div>' +
          '<div class="field"><label for="' + p + '-qty">Quantity <span class="req" aria-hidden="true">*</span></label>' +
            '<div class="stepper"><button type="button" data-step="-1" aria-label="Decrease quantity"' + (l.qty <= 1 ? ' disabled' : '') + '>&minus;</button>' +
            '<input id="' + p + '-qty" data-k="qty" type="number" inputmode="numeric" min="1" step="1" value="' + esc(l.qty) + '" aria-describedby="' + p + '-qty-err">' +
            '<button type="button" data-step="1" aria-label="Increase quantity">+</button></div>' +
            '<p class="field__err" id="' + p + '-qty-err"></p></div>' +
          '<div class="field"><label for="' + p + '-pressure">Pressure class</label><select id="' + p + '-pressure" data-k="pressure">' + options(PRESSURE, l.pressure) + '</select></div>' +
          '<div class="field"><label for="' + p + '-material">Material</label><select id="' + p + '-material" data-k="material">' + options(MATERIALS, l.material) + '</select></div>' +
          '<div class="field field--wide"><label for="' + p + '-notes">Notes <span class="opt">optional</span></label>' +
            '<textarea id="' + p + '-notes" data-k="notes" rows="2" placeholder="End connection, fluid, temperature, mesh, delivery location">' + esc(l.notes) + '</textarea></div>' +
        '</div>' +
      '</div>';
  }

  function findLine(id) { return lines.filter(function (l) { return l.id === id; })[0]; }

  function addLine(data, opts) {
    var l = {
      id: ++seq, name: data.name || '', custom: !!data.custom, size: data.size || '', unit: data.unit || 'in',
      pressure: 'Not sure', material: data.material || 'Not sure', qty: 1, notes: '', source: data.source || null
    };
    lines.push(l);
    var li = document.createElement('li');
    li.className = 'line' + (reduceMotion.matches ? '' : ' is-new');
    li.dataset.id = l.id;
    li.setAttribute('aria-label', 'Line ' + lines.length);
    li.innerHTML = lineHTML(l);
    linesEl.appendChild(li);
    updateCounts(true);
    hideReview();
    if (opts && opts.focus) { var f = $('input, select', li); if (f) f.focus(); }
    return l;
  }

  function removeLine(id, opts) {
    var idx = lines.findIndex(function (l) { return l.id === id; });
    if (idx === -1) return;
    var l = lines[idx];
    lines.splice(idx, 1);
    var li = $('.line[data-id="' + id + '"]', linesEl);
    var next = li && (li.nextElementSibling || li.previousElementSibling);
    if (l.source) setAdded(l.source, false);
    updateCounts(false);
    hideReview();
    var done = function () {
      if (li) li.remove();
      updateCounts(false);
      if (opts && opts.focus) {
        var target = next && next.isConnected ? $('.line__remove', next) : $('#add-custom');
        target.focus();
      }
    };
    if (li && !reduceMotion.matches) { li.classList.add('is-removing'); setTimeout(done, 220); } else done();
  }

  function setAdded(btn, on) {
    btn.setAttribute('aria-pressed', String(on));
    $('.btn--add__label', btn).textContent = on ? 'Added to quote' : 'Add to quote';
    var card = btn.closest('.range-card');
    if (card) card.classList.toggle('is-added', on);
  }

  // Give every add button an accessible item name after the visible label
  $$('[data-add]').forEach(function (btn) {
    var sr = document.createElement('span');
    sr.className = 'sr-only';
    sr.textContent = ': ' + btn.dataset.add;
    btn.appendChild(sr);
    btn.addEventListener('click', function () {
      var existing = lines.filter(function (l) { return l.source === btn; })[0];
      if (existing) {
        removeLine(existing.id);
        showToast('Removed from your request sheet.');
        return;
      }
      addLine({ name: btn.dataset.add, size: btn.dataset.size, unit: btn.dataset.unit, material: btn.dataset.material, source: btn });
      setAdded(btn, true);
      showToast('Added to your request sheet. Press again to remove.');
    });
  });

  $('#add-custom').addEventListener('click', function () { addLine({ custom: true }, { focus: true }); });

  // Line field editing (event delegation)
  linesEl.addEventListener('input', function (e) {
    var li = e.target.closest('.line'); if (!li) return;
    var l = findLine(Number(li.dataset.id)); var k = e.target.dataset.k; if (!l || !k) return;
    if (k === 'qty') {
      var n = parseInt(e.target.value, 10);
      l.qty = isNaN(n) ? e.target.value : n;
      $('[data-step="-1"]', li).disabled = !(n > 1);
    } else {
      l[k] = e.target.value;
      if (k === 'name') { var rb = $('.line__remove', li); rb.setAttribute('aria-label', 'Remove ' + (l.name || 'this line')); }
    }
    if (e.target.getAttribute('aria-invalid') === 'true') validateLine(l, li);
    hideReview();
  });
  linesEl.addEventListener('change', function (e) {
    if (e.target.tagName === 'SELECT') {
      var li = e.target.closest('.line'); var l = findLine(Number(li.dataset.id)); l[e.target.dataset.k] = e.target.value; hideReview();
    }
  });
  linesEl.addEventListener('click', function (e) {
    var rm = e.target.closest('[data-remove]');
    if (rm) { removeLine(Number(rm.dataset.remove), { focus: true }); return; }
    var st = e.target.closest('[data-step]');
    if (st) {
      var li = st.closest('.line'); var l = findLine(Number(li.dataset.id));
      var input = $('[data-k="qty"]', li);
      var cur = parseInt(input.value, 10); if (isNaN(cur) || cur < 1) cur = 1;
      var nv = Math.max(1, Math.min(99999, cur + Number(st.dataset.step)));
      input.value = nv; l.qty = nv;
      $('[data-step="-1"]', li).disabled = nv <= 1;
      if (input.getAttribute('aria-invalid') === 'true') validateLine(l, li);
      hideReview();
    }
  });

  /* ---------------- Validation ---------------- */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  function contactKind(v) {
    v = v.trim();
    if (!v) return null;
    if (v.indexOf('@') !== -1) return EMAIL_RE.test(v) ? 'email' : null;
    if (!/^[+()\d\s.-]+$/.test(v)) return null;
    var digits = v.replace(/\D/g, '');
    if (v.indexOf('+') > 0) return null;
    return digits.length >= 7 && digits.length <= 15 ? 'phone' : null;
  }
  window.__contactKind = contactKind; // exposed for the test suite only

  function setErr(input, errEl, msg) {
    if (msg) { input.setAttribute('aria-invalid', 'true'); errEl.textContent = msg; }
    else { input.removeAttribute('aria-invalid'); errEl.textContent = ''; }
    return !msg;
  }

  function validateLine(l, li) {
    var errs = [];
    if (l.custom) {
      var nIn = $('[data-k="name"]', li);
      var okN = setErr(nIn, $('#l' + l.id + '-name-err'), l.name.trim() ? '' : 'Enter what you need for this line.');
      if (!okN) errs.push({ el: nIn, msg: 'Line ' + (lines.indexOf(l) + 1) + ': enter the item' });
    }
    var qIn = $('[data-k="qty"]', li);
    var q = Number(qIn.value);
    var okQ = setErr(qIn, $('#l' + l.id + '-qty-err'), Number.isInteger(q) && q >= 1 ? '' : 'Enter a whole number, 1 or more.');
    if (!okQ) errs.push({ el: qIn, msg: 'Line ' + (lines.indexOf(l) + 1) + ': quantity must be a whole number, 1 or more' });
    return errs;
  }

  var nameIn = $('#c-name'), companyIn = $('#c-company'), contactIn = $('#c-contact');
  function validateContact() {
    var errs = [];
    if (!setErr(nameIn, $('#c-name-err'), nameIn.value.trim() ? '' : 'Enter your name.')) errs.push({ el: nameIn, msg: 'Enter your name' });
    var raw = contactIn.value.trim();
    var msg = !raw ? 'Enter an email address or a phone number.'
      : contactKind(raw) ? ''
      : raw.indexOf('@') !== -1 ? 'Check the email address, for example name@company.com.'
      : 'Check the phone number. Use digits, with the country code if outside the UAE.';
    if (!setErr(contactIn, $('#c-contact-err'), msg)) errs.push({ el: contactIn, msg: msg.replace(/\.$/, '') });
    return errs;
  }
  [nameIn, contactIn].forEach(function (inp) {
    inp.addEventListener('blur', function () { if (inp.value.trim() || inp.getAttribute('aria-invalid') === 'true') validateContact(); });
    inp.addEventListener('input', function () { if (inp.getAttribute('aria-invalid') === 'true') validateContact(); hideReview(); });
  });
  companyIn.addEventListener('input', hideReview);

  var summaryEl = $('#error-summary');
  function showSummary(errs) {
    var ul = $('ul', summaryEl);
    ul.innerHTML = '';
    errs.forEach(function (er) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + er.el.id;
      a.textContent = er.msg;
      a.addEventListener('click', function (ev) { ev.preventDefault(); er.el.focus(); er.el.scrollIntoView({ block: 'center', behavior: reduceMotion.matches ? 'auto' : 'smooth' }); });
      li.appendChild(a); ul.appendChild(li);
    });
    summaryEl.hidden = false;
  }

  /* ---------------- Review + copy ---------------- */
  function buildText() {
    var out = [];
    out.push('Quote request for Pipeline Products Online');
    out.push('To: websales@pipelineproductsonline.com');
    out.push('');
    out.push('Items');
    lines.forEach(function (l, i) {
      out.push((i + 1) + '. ' + l.name.trim());
      var bits = [];
      bits.push('Size: ' + (l.size.trim() ? l.size.trim() + ' ' + (l.unit === 'in' ? 'inch' : l.unit) : 'not given'));
      bits.push('Pressure class: ' + l.pressure);
      bits.push('Material: ' + l.material);
      bits.push('Quantity: ' + l.qty);
      out.push('   ' + bits.join('; '));
      if (l.notes.trim()) out.push('   Notes: ' + l.notes.trim());
    });
    out.push('');
    out.push('Contact');
    out.push('Name: ' + nameIn.value.trim());
    if (companyIn.value.trim()) out.push('Company: ' + companyIn.value.trim());
    var c = contactIn.value.trim();
    out.push((contactKind(c) === 'email' ? 'Email: ' : 'Phone: ') + c);
    out.push('');
    out.push('Please confirm price, availability and suitability.');
    return out.join('\n');
  }

  var copyBtn = $('#copy-btn'), copyStatus = $('#copy-status'), fallback = $('#copy-fallback'), fallbackText = $('#copy-fallback-text');
  function hideReview() {
    if (reviewEl.hidden) return;
    reviewEl.hidden = true;
    copyStatus.textContent = ''; copyStatus.className = 'review__status';
    fallback.hidden = true;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var errs = [];
    if (!lines.length) errs.push({ el: $('#add-custom'), msg: 'Add at least one item to the sheet' });
    lines.forEach(function (l) {
      errs = errs.concat(validateLine(l, $('.line[data-id="' + l.id + '"]', linesEl)));
    });
    errs = errs.concat(validateContact());

    if (errs.length) {
      showSummary(errs);
      hideReview();
      summaryEl.scrollIntoView({ block: 'center', behavior: reduceMotion.matches ? 'auto' : 'smooth' });
      errs[0].el.focus({ preventScroll: true });
      return;
    }
    summaryEl.hidden = true;
    $('#review-text').textContent = buildText();
    copyStatus.textContent = ''; copyStatus.className = 'review__status';
    fallback.hidden = true;
    reviewEl.hidden = false;
    reviewEl.focus({ preventScroll: true });
    reviewEl.scrollIntoView({ block: 'start', behavior: reduceMotion.matches ? 'auto' : 'smooth' });
  });

  function copyFailed() {
    copyStatus.className = 'review__status is-warn';
    copyStatus.textContent = 'Copying is blocked in this browser. Select the text below and copy it. Nothing has been sent.';
    fallbackText.value = buildText();
    fallback.hidden = false;
    fallbackText.focus();
    fallbackText.select();
  }

  copyBtn.addEventListener('click', function () {
    var text = buildText();
    copyStatus.textContent = ''; copyStatus.className = 'review__status';
    if (!navigator.clipboard || !window.isSecureContext) { copyFailed(); return; }
    navigator.clipboard.writeText(text).then(function () {
      fallback.hidden = true;
      copyStatus.className = 'review__status is-ok';
      copyStatus.textContent = 'Copied. Nothing has been sent.';
    }, copyFailed);
  });

  $('#edit-btn').addEventListener('click', function () {
    hideReview();
    var first = $('input, select', linesEl) || nameIn;
    first.focus();
  });
})();
