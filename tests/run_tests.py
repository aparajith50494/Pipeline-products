"""
Runs the 30 launch criteria in CRITERIA.md against the page.

  pip install playwright pillow
  python -m playwright install chromium
  python tests/run_tests.py

Starts its own local server, writes TEST-REPORT.md and screenshots/ in the project folder.
Nothing is sent anywhere: the only network traffic is to the local server and the
catalogue image URLs the page itself references.
"""
import json, re, socket, subprocess, sys, time, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

PORT = free_port()
URL = f"http://localhost:{PORT}/"
IMG_HOST = "pipelineproductsonline.com"

results = {}  # id -> (passed, detail)
def record(cid, ok, detail):
    results[cid] = (bool(ok), detail)
    print(f"{'PASS' if ok else 'FAIL'}  {cid}  {detail}")

def check(cid):
    def deco(fn):
        def run(*a, **k):
            try:
                ok, detail = fn(*a, **k)
            except Exception as e:  # a crashing check is a failing check
                ok, detail = False, f"error: {type(e).__name__}: {str(e)[:300]}"
            record(cid, ok, detail)
        run.cid = cid
        return run
    return deco

def settle(pg, ms=650):
    pg.wait_for_timeout(ms)

def scroll_through(pg):
    h = pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h, 350):
        pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(35)
    pg.wait_for_timeout(500)
    pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(400)

def visible_cards(pg):
    return pg.evaluate("[...document.querySelectorAll('.range-card')].filter(c=>!c.hidden).map(c=>c.id)")

def line_count(pg):
    return pg.evaluate("document.querySelectorAll('#sheet-lines .line:not(.is-removing)').length")

def badge(pg):
    return int(pg.evaluate("document.querySelector('[data-quote-num]').textContent"))

def new_page(browser, w=1280, h=800, reduced=False, js=True, clipboard=True, init=None):
    ctx = browser.new_context(viewport={"width": w, "height": h}, java_script_enabled=js,
                              reduced_motion="reduce" if reduced else "no-preference")
    if clipboard:
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=URL.rstrip("/"))
    if init:
        ctx.add_init_script(init)
    pg = ctx.new_page()
    pg.console_errors, pg.page_errors, pg.requests = [], [], []
    def on_console(m):
        if m.type == "error":
            loc = (m.location or {}).get("url", "")
            pg.console_errors.append({"text": m.text, "url": loc})
    pg.on("console", on_console)
    pg.on("pageerror", lambda e: pg.page_errors.append(str(e)))
    pg.on("request", lambda r: pg.requests.append({"url": r.url, "method": r.method, "type": r.resource_type}))
    pg.goto(URL, wait_until="load")
    settle(pg, 900)
    return pg

STORAGE_SPY = """
window.__storageWrites = 0;
const _set = Storage.prototype.setItem;
Storage.prototype.setItem = function(){ window.__storageWrites++; return _set.apply(this, arguments); };
"""
CLS_SPY = """
window.__cls = 0;
new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
  .observe({type: 'layout-shift', buffered: true});
"""

# ======================= APPEAL =======================

@check("A1")
def a1(b):
    pg = new_page(b, reduced=True)
    bad = pg.evaluate("""() => {
      const out = [];
      const toHsl = (r,g,b) => { r/=255; g/=255; b/=255; const mx=Math.max(r,g,b), mn=Math.min(r,g,b); let h=0,s=0; const l=(mx+mn)/2;
        if (mx!==mn){ const d=mx-mn; s = l>0.5? d/(2-mx-mn) : d/(mx+mn);
          h = mx===r ? (g-b)/d + (g<b?6:0) : mx===g ? (b-r)/d+2 : (r-g)/d+4; h*=60; } return [h,s,l]; };
      for (const el of document.querySelectorAll('*')) {
        const cs = getComputedStyle(el);
        for (const p of ['color','backgroundColor','borderTopColor','borderLeftColor','outlineColor']) {
          const m = cs[p].match(/rgba?\\((\\d+), (\\d+), (\\d+)(?:, ([\\d.]+))?\\)/); if (!m) continue;
          if (m[4] !== undefined && parseFloat(m[4]) === 0) continue;
          const [h,s,l] = toHsl(+m[1],+m[2],+m[3]);
          if (h >= 15 && h <= 48 && s > 0.45 && l > 0.25 && l < 0.8) out.push(el.tagName + '.' + el.className + ' ' + p + ' ' + cs[p]);
        }
      }
      return out;
    }""")
    css = (ROOT / "styles.css").read_text().lower()
    orange_hex = re.findall(r"#(?:e[0-9a-f]8|f[0-9a-f][5-9a-c])[0-9a-f]{2}0?\b", css)
    pg.context.close()
    return (not bad, f"orange-like computed colours: {len(bad)} {bad[:3]}")

@check("A2")
def a2(b):
    pg = new_page(b)
    r = pg.evaluate("""async () => { await document.fonts.ready;
      const body = getComputedStyle(document.body); const h1 = getComputedStyle(document.querySelector('h1'));
      return { loaded: document.fonts.check('16px Archivo'),
        family: body.fontFamily, fs: parseFloat(body.fontSize), lh: parseFloat(body.lineHeight),
        stretch: h1.fontStretch, faces: [...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family) }; }""")
    pg.context.close()
    stretch = float(r["stretch"].rstrip("%")) if r["stretch"].endswith("%") else 100
    ok = r["loaded"] and "Archivo" in "".join(r["faces"]) and r["fs"] >= 16 and r["lh"] / r["fs"] >= 1.5 and stretch <= 80
    return ok, f"Archivo loaded={r['loaded']}, body {r['fs']}px / line-height {r['lh']/r['fs']:.2f}, h1 width {r['stretch']}"

@check("A3")
def a3(b):
    pg = new_page(b, reduced=True)
    r = pg.evaluate("""() => { const c = document.createElement('canvas').getContext('2d'); const out=[];
      for (const p of document.querySelectorAll('main p, footer p')) {
        if (!p.offsetParent || p.textContent.trim().length < 90) continue;
        const cs = getComputedStyle(p); c.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
        const t = p.textContent.trim().replace(/\\s+/g,' '); const avg = c.measureText(t).width / t.length;
        const width = p.getBoundingClientRect().width;
        out.push({cpl: Math.round(width/avg), text: t.slice(0,40)}); }
      return out; }""")
    pg.context.close()
    worst = max(r, key=lambda x: x["cpl"])
    return worst["cpl"] <= 85, f"{len(r)} paragraphs checked, longest line about {worst['cpl']} characters ('{worst['text']}...')"

CONTRAST_JS = """() => {
  const parse = s => { const m = s.match(/rgba?\\(([\\d.]+), ([\\d.]+), ([\\d.]+)(?:, ([\\d.]+))?\\)/); return m ? [+m[1],+m[2],+m[3], m[4]===undefined?1:+m[4]] : null; };
  const lum = ([r,g,b]) => { const f = v => { v/=255; return v<=0.03928? v/12.92 : Math.pow((v+0.055)/1.055,2.4); }; return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); };
  const blend = (fg, bg) => [0,1,2].map(i => fg[i]*fg[3] + bg[i]*(1-fg[3]));
  const bgOf = el => { let stack=[]; for (let e=el; e; e=e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c[3]>0) { stack.push(c); if (c[3]===1) break; } }
    let col=[255,255,255]; for (let i=stack.length-1;i>=0;i--) col = blend(stack[i], col); return col; };
  const fails=[]; let n=0;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const t = walker.currentNode; if (!t.textContent.trim()) continue; const el = t.parentElement; if (seen.has(el)) continue; seen.add(el);
    if (el.closest('.sr-only, [hidden], noscript, script, style, .skip-link, option, .toast')) continue;
    const r = el.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el); if (cs.visibility==='hidden' || +cs.opacity===0) continue;
    if (el.closest('[aria-hidden="true"]')) continue;
    const fg = parse(cs.color); let bg = bgOf(el);
    const ind = el.closest('.has-indicator') && el.matches('.chip[aria-pressed="true"]') && el.parentElement.querySelector('.filter__indicator');
    if (ind) { const a = ind.getBoundingClientRect(), c = el.getBoundingClientRect();
      if (Math.abs(a.left-c.left) < 2 && Math.abs(a.width-c.width) < 2 && Math.abs(a.top-c.top) < 2) bg = parse(getComputedStyle(ind).backgroundColor).slice(0,3); }
    const f = blend(fg, bg);
    const L1 = lum(f), L2 = lum(bg); const ratio = (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
    const fs = parseFloat(cs.fontSize), fw = parseInt(cs.fontWeight);
    const large = fs >= 24 || (fs >= 18.66 && fw >= 700);
    n++; if (ratio < (large ? 3 : 4.5)) fails.push(`${el.tagName}.${el.className} "${t.textContent.trim().slice(0,30)}" ${ratio.toFixed(2)}`);
  }
  return {n, fails};
}"""

@check("A4")
def a4(b):
    out = []
    total = 0
    for w, h in [(1280, 800), (390, 844)]:
        pg = new_page(b, w, h, reduced=True)
        pg.evaluate("document.querySelector('#kraissl-details-toggle').click()"); settle(pg, 100)
        r = pg.evaluate(CONTRAST_JS); total += r["n"]; out += r["fails"]
        pg.context.close()
    return not out, f"{total} text elements checked at two widths, {len(out)} below AA {out[:3]}"

@check("A5")
def a5(b):
    pg = new_page(b)
    pads = pg.evaluate("[...document.querySelectorAll('main > .section')].map(s=>getComputedStyle(s).paddingTop+'/'+getComputedStyle(s).paddingBottom)")
    pg.context.close()
    return len(set(pads)) == 1, f"{len(pads)} sections share padding {set(pads)}"

@check("A6")
def a6(b):
    notes, ok = [], True
    for w, h in [(320, 640), (390, 844), (1280, 800)]:
        pg = new_page(b, w, h); settle(pg, 700)
        r = pg.evaluate("""() => { const h1=document.querySelector('h1'); const a=document.querySelector('.hero__actions');
          const btns=[...a.querySelectorAll('.btn')].map(x=>x.getBoundingClientRect());
          return { clip: h1.scrollWidth > h1.clientWidth + 1, right: Math.max(...btns.map(r=>r.right), h1.getBoundingClientRect().right),
                   bottom: Math.max(...btns.map(r=>r.bottom)), vw: innerWidth, vh: innerHeight }; }""")
        good = not r["clip"] and r["right"] <= r["vw"] + 0.5
        if (w, h) != (320, 640): good = good and r["bottom"] <= r["vh"]
        ok &= good
        notes.append(f"{w}px: actions bottom {round(r['bottom'])}/{r['vh']}{'' if good else ' FAIL'}")
        pg.screenshot(path=str(SHOTS / f"hero-{w}.png"))
        pg.context.close()
    return ok, "; ".join(notes)

@check("A7")
def a7(b):
    pg = new_page(b)
    scroll_through(pg); settle(pg, 800)
    r = pg.evaluate("""() => [...document.querySelectorAll('img[data-fallback]')].map(img => { const f = img.closest('.frame');
      const fcs = getComputedStyle(f); const ics = getComputedStyle(img);
      return { name: img.dataset.fallback, loaded: img.naturalWidth > 0 && !img.hidden, fallback: !!f.querySelector('.img-fallback'),
               fallbackText: (f.querySelector('.img-fallback')||{}).textContent || '', fit: ics.objectFit,
               hero: f.classList.contains('frame--hero'), ratio: fcs.aspectRatio, dims: img.hasAttribute('width') && img.hasAttribute('height'),
               alt: img.alt.length > 10 }; })""")
    pg.context.close()
    problems = []
    for i in r:
        if not (i["loaded"] or (i["fallback"] and i["name"] in i["fallbackText"])): problems.append(i["name"] + " neither loaded nor labelled")
        if i["fit"] != ("cover" if i["hero"] else "contain"): problems.append(i["name"] + " object-fit " + i["fit"])
        if i["ratio"] in ("auto", ""): problems.append(i["name"] + " no aspect ratio")
        if not i["dims"] or not i["alt"]: problems.append(i["name"] + " missing dimensions or alt")
    loaded = sum(1 for i in r if i["loaded"]); fb = sum(1 for i in r if i["fallback"])
    return not problems, f"{len(r)} images: {loaded} loaded, {fb} labelled placeholders. {problems[:3]}"

@check("A8")
def a8(b):
    pg = new_page(b)
    pg.locator("#item-y-ci").scroll_into_view_if_needed(); settle(pg, 800)
    r = pg.evaluate("""() => { const d = (el, prop) => { const cs = getComputedStyle(el); const props = cs.transitionProperty.split(',').map(s=>s.trim());
        const durs = cs.transitionDuration.split(',').map(s=>parseFloat(s)*1000); const i = props.indexOf(prop); return i<0 ? (props[0]==='all'?durs[0]:null) : durs[i % durs.length]; };
      const probe = document.createElement('div'); probe.className='reveal'; document.body.appendChild(probe);
      const out = { button: d(document.querySelector('.btn'),'transform'), chip: d(document.querySelector('.chip'),'transform'),
        card: d(document.getElementById('item-y-ci'),'transform'), mchip: d(document.querySelector('.mchip'),'transform'),
        reveal: d(probe,'opacity'), disclosure: d(document.querySelector('.disclosure'),'grid-template-rows') };
      probe.remove(); return out; }""")
    pg.context.close()
    ui = [r["button"], r["chip"], r["card"], r["mchip"]]
    ok = all(v is not None and 160 <= v <= 240 for v in ui) and 300 <= r["reveal"] <= 500 and 300 <= r["disclosure"] <= 500
    return ok, f"hover/press {ui} ms, reveal {r['reveal']} ms, details panel {r['disclosure']} ms"

@check("A9")
def a9(b):
    pg = new_page(b, reduced=True)
    r = pg.evaluate("""() => ({ dur: parseFloat(getComputedStyle(document.querySelector('.btn')).transitionDuration)*1000,
       reveals: document.querySelectorAll('.reveal').length, hero: getComputedStyle(document.querySelector('.hero__title-inner')).transform,
       hidden: [...document.querySelectorAll('.section-head, .range-card, .hero__lede')].filter(e => +getComputedStyle(e).opacity < 1).length,
       smooth: getComputedStyle(document.documentElement).scrollBehavior })""")
    pg.context.close()
    ok = r["dur"] <= 0.02 and r["reveals"] == 0 and r["hero"] == "none" and r["hidden"] == 0 and r["smooth"] == "auto"
    return ok, f"transition {r['dur']} ms, reveal classes {r['reveals']}, hidden blocks {r['hidden']}, scroll-behavior {r['smooth']}"

@check("A10")
def a10(b):
    pg = new_page(b)
    r = pg.evaluate("""() => { const rules=[]; for (const s of document.styleSheets) for (const r of s.cssRules) if (r.selectorText) rules.push(r);
      const find = sel => rules.filter(r => r.selectorText.split(',').map(x=>x.trim()).includes(sel));
      const pick = sel => find(sel).map(r => ({t: r.style.transform, layout: ['width','height','margin','top','left','padding'].some(p => r.style[p])}));
      return { press: pick('.btn:active'), lift: pick('.range-card:hover'), line: pick('.line-card:hover'), chip: pick('.chip:active') }; }""")
    pg.context.close()
    def good(lst, word): return lst and all(x["t"] and word in x["t"] and not x["layout"] for x in lst)
    ok = good(r["press"], "scale") and good(r["lift"], "translateY") and good(r["line"], "translateY") and good(r["chip"], "scale")
    return ok, f"press {r['press'][0]['t'] if r['press'] else None}; card lift {r['lift'][0]['t'] if r['lift'] else None}; transform only"

@check("A11")
def a11(b):
    vals = []
    for w, h in [(1280, 800), (390, 844)]:
        pg = new_page(b, w, h, init=CLS_SPY); settle(pg, 1800)
        vals.append(pg.evaluate("window.__cls")); pg.context.close()
    return max(vals) < 0.05, f"CLS desktop {vals[0]:.4f}, mobile {vals[1]:.4f}"

@check("A12")
def a12(b):
    notes, ok = [], True
    for w in (320, 390, 1280):
        pg = new_page(b, w, 800)
        pg.click("#add-custom"); settle(pg, 200)
        pg.locator("#range .btn--add").first.click(); settle(pg, 300)
        scroll_through(pg)
        over = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
        if w < 941:
            pg.click(".menu-toggle"); settle(pg, 300)
            over = max(over, pg.evaluate("document.documentElement.scrollWidth - innerWidth"))
        ok &= over <= 0; notes.append(f"{w}px overflow {over}px")
        pg.context.close()
    return ok, "; ".join(notes)

@check("A13")
def a13(b):
    pg = new_page(b, 390, 844, reduced=True)
    pg.click("#add-custom"); pg.click("#kraissl-details-toggle"); pg.click(".mchip >> nth=0"); settle(pg, 200)
    pg.evaluate("document.querySelector('.contact__people').open = true")
    small = pg.evaluate("""() => [...document.querySelectorAll('a[href], button, input, select, textarea, summary')].filter(e => {
        if (e.closest('.sr-only, [hidden]') || e.classList.contains('skip-link')) return false;
        const cs = getComputedStyle(e); if (cs.visibility==='hidden' || cs.display==='none') return false;
        if (e.closest('p') && e.tagName==='A') return false;  // inline links within sentences are exempt (WCAG 2.5.8)
        const r = e.getBoundingClientRect(); if (!r.width) return false;
        return r.height < 44 || r.width < 44; }).map(e => `${e.tagName}.${e.className} ${Math.round(e.getBoundingClientRect().width)}x${Math.round(e.getBoundingClientRect().height)}`)""")
    total = pg.evaluate("document.querySelectorAll('a[href], button, input, select, textarea, summary').length")
    pg.context.close()
    return not small, f"{total} controls, {len(small)} under 44px {small[:4]}"

@check("A14")
def a14(b):
    pg = new_page(b, reduced=True)
    pg.click("#add-custom"); settle(pg, 100)
    pg.evaluate("window.scrollTo(0,0); document.querySelector('.skip-link').focus()")
    missing, seen = [], 0
    for _ in range(140):
        pg.keyboard.press("Tab")
        r = pg.evaluate("""() => { const e = document.activeElement; if (!e || e===document.body) return null; const cs = getComputedStyle(e);
          const ring = (cs.outlineStyle!=='none' && parseFloat(cs.outlineWidth) >= 2) || /\\d+px \\d+px 0px [3-9]px|0px 0px 0px [2-9]px/.test(cs.boxShadow);
          return { id: e.id || e.className || e.tagName, ring, fv: e.matches(':focus-visible'), end: e === [...document.querySelectorAll('footer a')].pop() }; }""")
        if not r: continue
        seen += 1
        if not (r["ring"] and r["fv"]): missing.append(r["id"])
        if r["end"]: break
    pg.context.close()
    return seen > 50 and not missing, f"{seen} focus stops checked, {len(missing)} without a visible ring {missing[:4]}"

@check("A15")
def a15(b):
    pg = new_page(b, reduced=True)
    r = pg.evaluate("""() => { const upper=[], grad=[], glass=[];
      for (const e of document.querySelectorAll('body *')) { const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
        if (cs.textTransform==='uppercase' && e.textContent.trim()) upper.push(e.className);
        if (/gradient/.test(cs.backgroundImage) && r.width>120 && r.height>120 && !e.classList.contains('img-fallback')) grad.push(e.className);
        if (cs.backdropFilter && cs.backdropFilter!=='none') glass.push(e.className); }
      const emoji = /[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}]/u.test(document.body.innerText);
      return {upper, grad, glass, emoji, arrows: /\\u2192/.test(document.body.innerText), dots: / \\u00b7 /.test(document.body.innerText)}; }""")
    pg.context.close()
    ok = not (r["upper"] or r["grad"] or r["glass"] or r["emoji"] or r["arrows"] or r["dots"])
    return ok, f"all-caps {len(r['upper'])}, gradient washes {len(r['grad'])}, glass {len(r['glass'])}, emoji {r['emoji']}, arrow-suffixed labels {r['arrows']}. Visual review: see screenshots/"

# ======================= FUNCTION =======================

@check("F1")
def f1(b):
    pg = new_page(b)
    r = pg.evaluate("""() => { const noname=[], broken=[];
      const name = e => (e.getAttribute('aria-label') || e.textContent || (e.getAttribute('aria-labelledby') && document.getElementById(e.getAttribute('aria-labelledby'))?.textContent) || '').trim();
      for (const e of document.querySelectorAll('a, button')) if (!name(e)) noname.push(e.outerHTML.slice(0,80));
      for (const a of document.querySelectorAll('a[href^="#"]')) { const id = a.getAttribute('href').slice(1); if (id && !document.getElementById(id)) broken.push(a.getAttribute('href')); }
      return { noname, broken, n: document.querySelectorAll('a, button').length }; }""")
    pg.context.close()
    return not r["noname"] and not r["broken"], f"{r['n']} links and buttons; unnamed {len(r['noname'])}; broken anchors {r['broken']}"

@check("F2")
def f2(b):
    pg = new_page(b)
    expected = {"all": 15, "y": 5, "basket": 4, "duplex": 4, "automatic": 2}
    notes, ok = [], True
    for f, n in [("y", 5), ("basket", 4), ("duplex", 4), ("automatic", 2), ("all", 15)]:
        pg.click(f'.chip[data-filter="{f}"]'); settle(pg, 450)
        got = len(visible_cards(pg))
        types = set(pg.evaluate("[...document.querySelectorAll('.range-card')].filter(c=>!c.hidden).map(c=>c.dataset.type)"))
        pressed = pg.get_attribute(f'.chip[data-filter="{f}"]', "aria-pressed")
        others = pg.evaluate(f"[...document.querySelectorAll('.chip:not([data-filter=\"{f}\"])')].every(c=>c.getAttribute('aria-pressed')==='false')")
        count = pg.text_content("#range-count")
        good = got == n and pressed == "true" and others and str(n) in count and (f == "all" or types == {f})
        ok &= good; notes.append(f"{f}={got}")
        if f == "duplex": pg.locator("#range").screenshot(path=str(SHOTS / "range-filtered-duplex.png"))
    live = pg.get_attribute("#range-count", "aria-live")
    pg.context.close()
    return ok and live == "polite", f"counts {', '.join(notes)}; aria-live={live}"

@check("F3")
def f3(b):
    pg = new_page(b, reduced=True)
    btns = pg.locator("#range .btn--add"); n = btns.count(); bad = []
    for i in range(n):
        btns.nth(i).click(); settle(pg, 30)
        if line_count(pg) != i + 1 or badge(pg) != i + 1 or btns.nth(i).get_attribute("aria-pressed") != "true": bad.append(f"add {i}")
    names = pg.evaluate("[...document.querySelectorAll('.line__name')].map(e=>e.textContent)")
    expected = pg.evaluate("[...document.querySelectorAll('#range .btn--add')].map(b=>b.dataset.add)")
    if names != expected: bad.append("line names differ from listings")
    pg.locator("#range").screenshot(path=str(SHOTS / "range-all-added.png"))
    for i in range(n):
        btns.nth(i).click(); settle(pg, 30)
        if line_count(pg) != n - i - 1 or btns.nth(i).get_attribute("aria-pressed") != "false": bad.append(f"remove {i}")
    pg.context.close()
    return not bad and n == 15, f"{n} cards added then removed; header count tracked each step. issues {bad[:3]}"

@check("F4")
def f4(b):
    pg = new_page(b, reduced=True)
    pg.click("#kraissl-add"); settle(pg, 50)
    line = pg.evaluate("""() => { const l = document.querySelector('#sheet-lines .line'); return l && { name: l.querySelector('.line__name').textContent,
        size: l.querySelector('[data-k=size]').value, unit: l.querySelector('[data-k=unit]').value, mat: l.querySelector('[data-k=material]').value }; }""")
    t = pg.locator("#kraissl-details-toggle")
    t.click(); settle(pg, 50)
    open1 = t.get_attribute("aria-expanded") == "true" and pg.is_visible("#kraissl-details .disclosure__content")
    pg.locator("#featured").screenshot(path=str(SHOTS / "featured-details-open.png"))
    t.focus(); pg.keyboard.press("Enter"); settle(pg, 50)
    closed = t.get_attribute("aria-expanded") == "false" and pg.is_hidden("#kraissl-details")
    pg.keyboard.press("Space"); settle(pg, 50)
    reopened = t.get_attribute("aria-expanded") == "true"
    ok = line and "Kraissl" in line["name"] and line["size"] == "1-1/2" and line["unit"] == "in" and line["mat"] == "Cast iron" and open1 and closed and reopened
    pg.context.close()
    return ok, f"line {line}; details open={open1}, keyboard close={closed}, keyboard reopen={reopened}"

@check("F5")
def f5(b):
    pg = new_page(b, reduced=True)
    expected = {"carbon-steel": 2, "stainless": 3, "ductile": 2, "cast-iron": 2, "bronze": 3, "al-bronze": 1}
    bad = []
    for m, n in expected.items():
        pg.click(f'.mchip[data-material="{m}"]'); settle(pg, 60)
        got = pg.locator("#materials-out .materials__jump").count()
        txt = pg.text_content("#materials-out").lower()
        if got != n: bad.append(f"{m}: {got}")
        if re.search(r"\b(suitable|compatible|recommended|best for)\b", txt): bad.append(f"{m}: advice wording")
    pg.locator("#materials").screenshot(path=str(SHOTS / "materials-selected.png"))
    pg.click('.chip[data-filter="duplex"]'); settle(pg, 300)   # target card is hidden by the filter
    pg.click('.mchip[data-material="al-bronze"]'); settle(pg, 60)
    if pg.get_attribute('.mchip[data-material="al-bronze"]', "aria-pressed") == "false":
        pg.click('.mchip[data-material="al-bronze"]'); settle(pg, 60)
    pg.click("#materials-out .materials__jump"); settle(pg, 500)
    r = pg.evaluate("""() => { const c = document.getElementById('item-y-ab'); const r = c.getBoundingClientRect();
        return { hidden: c.hidden, flash: c.classList.contains('is-flash'), inView: r.top >= 0 && r.bottom <= innerHeight, focus: c.contains(document.activeElement) }; }""")
    pg.click('.mchip[data-material="al-bronze"]'); settle(pg, 60)
    cleared = pg.locator("#materials-out .materials__jump").count() == 0
    pg.context.close()
    ok = not bad and not r["hidden"] and r["flash"] and r["inView"] and r["focus"] and cleared
    return ok, f"listing counts correct for 6 materials; jump un-hid the card, scrolled, highlighted and focused: {r}; toggle off clears: {cleared}. {bad}"

@check("F6")
def f6(b):
    pg = new_page(b, reduced=True)
    pg.click("#add-custom"); settle(pg, 50)
    L = "#sheet-lines .line >> nth=0 >> "
    pg.fill(L + "[data-k=name]", "Gate valve, flanged")
    pg.fill(L + "[data-k=size]", "50")
    pg.select_option(L + "[data-k=unit]", "mm")
    pg.select_option(L + "[data-k=pressure]", "Class 300")
    pg.select_option(L + "[data-k=material]", "Stainless steel / 316SS")
    minus_disabled_at_1 = pg.is_disabled(L + '[data-step="-1"]')
    pg.click(L + '[data-step="1"]'); pg.click(L + '[data-step="1"]'); pg.click(L + '[data-step="-1"]')
    qty = pg.input_value(L + "[data-k=qty]")
    pg.fill(L + "[data-k=notes]", "Water service")
    pg.click('#range .btn--add >> nth=0'); settle(pg, 50)
    nums = pg.evaluate("[...document.querySelectorAll('.line__num')].map(e=>e.textContent)")
    pg.locator("#quote").screenshot(path=str(SHOTS / "quote-lines.png"))
    pg.click("#sheet-lines .line >> nth=0 >> .line__remove"); settle(pg, 300)
    after = line_count(pg)
    renum = pg.evaluate("[...document.querySelectorAll('.line__num')].map(e=>e.textContent)")
    focus_ok = pg.evaluate("document.activeElement.classList.contains('line__remove') || document.activeElement.id==='add-custom'")
    pg.context.close()
    ok = minus_disabled_at_1 and qty == "2" and nums == ["1", "2"] and after == 1 and renum == ["1"] and focus_ok
    return ok, f"stepper min 1 enforced={minus_disabled_at_1}, qty after +,+,- = {qty}, numbering {nums} -> {renum} after removal, focus kept={focus_ok}"

@check("F7")
def f7(b):
    pg = new_page(b, 390, 844, reduced=True, init=STORAGE_SPY)
    pg.click("#add-custom"); pg.fill("#sheet-lines [data-k=name]", "Ball valve"); pg.fill("#sheet-lines [data-k=size]", "3")
    pg.fill("#c-name", "Test Buyer"); pg.fill("#c-contact", "buyer@example.com")
    pg.click('.chip[data-filter="y"]'); settle(pg, 200)
    pg.click(".menu-toggle"); pg.click('#primary-nav a[href="#brands"]'); settle(pg, 300)
    pg.click('#range .range-card:not([hidden]) .btn--add >> nth=0')
    pg.evaluate("window.scrollTo(0,0)"); settle(pg, 100)
    kept = pg.evaluate("""() => ({ item: document.querySelector('#sheet-lines [data-k=name]').value, size: document.querySelector('#sheet-lines [data-k=size]').value,
        name: document.getElementById('c-name').value, contact: document.getElementById('c-contact').value, lines: document.querySelectorAll('#sheet-lines .line').length,
        ls: localStorage.length, ss: sessionStorage.length, writes: window.__storageWrites })""")
    pg.context.close()
    ok = kept["item"] == "Ball valve" and kept["size"] == "3" and kept["name"] == "Test Buyer" and kept["contact"] == "buyer@example.com" and kept["lines"] == 2 and kept["ls"] == 0 and kept["ss"] == 0 and kept["writes"] == 0
    return ok, f"after filtering, menu navigation and adding: {kept}"

@check("F8")
def f8(b):
    pg = new_page(b, reduced=True)
    pg.click("#review-btn"); settle(pg, 100)
    s1 = pg.is_visible("#error-summary"); f1_ = pg.evaluate("document.activeElement.id")
    items = pg.locator("#error-summary li").count()
    pg.click("#add-custom"); pg.fill("#sheet-lines [data-k=qty]", "0")
    pg.click("#review-btn"); settle(pg, 100)
    inv = pg.evaluate("[...document.querySelectorAll('[aria-invalid=true]')].map(e=>e.id)")
    first = pg.evaluate("document.activeElement.id")
    msgs = pg.evaluate("[...document.querySelectorAll('.field__err')].map(e=>e.textContent).filter(Boolean)")
    pg.locator("#quote").screenshot(path=str(SHOTS / "quote-validation.png"))
    link_ok = True
    pg.click("#error-summary a >> nth=2"); settle(pg, 100)
    link_ok = pg.evaluate("document.activeElement.id") == "c-name"
    review_hidden = pg.is_hidden("#review")
    pg.context.close()
    ok = s1 and f1_ == "add-custom" and items == 3 and len(inv) == 4 and first == inv[0] and len(msgs) == 4 and link_ok and review_hidden
    return ok, f"empty sheet: summary shown with {items} items, focus on {f1_}; invalid fields {inv}; focus moved to {first}; summary links focus fields={link_ok}"

@check("F9")
def f9(b):
    pg = new_page(b)
    cases = {"buyer@company.ae": "email", "+971 50 769 6794": "phone", "06 566 4727": "phone", "(050) 769-6794": "phone",
             "buyer@company": None, "hello": None, "12345": None, "+971 50 abc 1234": None}
    got = {k: pg.evaluate("v => window.__contactKind(v)", k) for k in cases}
    pg.fill("#c-contact", "not an email@"); pg.click("#review-btn"); settle(pg, 50)
    msg = pg.text_content("#c-contact-err")
    pg.context.close()
    wrong = {k: v for k, v in got.items() if v != cases[k]}
    return not wrong and "email" in msg.lower(), f"8 inputs classified correctly={not wrong} {wrong}; error text: '{msg}'"

def fill_full(pg):
    pg.click("#kraissl-add"); pg.click('.chip[data-filter="duplex"]'); settle(pg, 200)
    pg.click("#item-d-50 .btn--add"); settle(pg, 50)
    L2 = "#sheet-lines .line >> nth=1 >> "
    pg.fill(L2 + "[data-k=size]", "4"); pg.select_option(L2 + "[data-k=pressure]", "Class 150")
    pg.click(L2 + '[data-step="1"]'); pg.click(L2 + '[data-step="1"]')
    pg.fill(L2 + "[data-k=notes]", "Seawater, flanged ends")
    pg.fill("#c-name", "Test Buyer"); pg.fill("#c-company", "Example Contracting LLC"); pg.fill("#c-contact", "+971 50 123 4567")

@check("F10")
def f10(b):
    pg = new_page(b, reduced=True)
    fill_full(pg); pg.click("#review-btn"); settle(pg, 100)
    t = pg.text_content("#review-text")
    need = ["Kraissl double basket strainer", "Size: 1-1/2 inch", "Material: Cast iron", "Eaton Model 50", "Size: 4 inch",
            "Pressure class: Class 150", "Quantity: 3", "Notes: Seawater, flanged ends", "Name: Test Buyer",
            "Company: Example Contracting LLC", "Phone: +971 50 123 4567", "websales@pipelineproductsonline.com"]
    miss = [n for n in need if n not in t]
    focus = pg.evaluate("document.activeElement.id")
    pg.locator("#quote").screenshot(path=str(SHOTS / "quote-review.png"))
    pg.fill("#c-name", "Changed"); settle(pg, 50)
    stale_hidden = pg.is_hidden("#review")
    pg.context.close()
    return not miss and focus == "review" and stale_hidden, f"summary has all {len(need)} expected values (missing {miss}); review gets focus; editing hides a stale review={stale_hidden}"

@check("F11")
def f11(b):
    # success path
    pg = new_page(b, reduced=True)
    start = len(pg.requests)
    fill_full(pg); pg.click("#review-btn"); settle(pg, 100)
    status_before = pg.text_content("#copy-status")
    pg.click("#copy-btn"); settle(pg, 300)
    status = pg.text_content("#copy-status")
    clip = pg.evaluate("navigator.clipboard.readText()")
    review = pg.text_content("#review-text")
    pg.locator("#quote").screenshot(path=str(SHOTS / "quote-copied.png"))
    flow_reqs = [r for r in pg.requests[start:] if not (r["type"] == "image" and IMG_HOST in r["url"])]
    pg.context.close()
    # failure path
    fail_init = "Object.defineProperty(navigator, 'clipboard', { value: { writeText: () => Promise.reject(new Error('denied')) } });"
    pg = new_page(b, reduced=True, init=fail_init)
    start2 = len(pg.requests)
    fill_full(pg); pg.click("#review-btn"); settle(pg, 100)
    pg.click("#copy-btn"); settle(pg, 300)
    st2 = pg.text_content("#copy-status")
    fb = pg.is_visible("#copy-fallback")
    sel = pg.evaluate("(() => { const t = document.getElementById('copy-fallback-text'); return document.activeElement===t && t.selectionStart===0 && t.selectionEnd===t.value.length && t.value.length>100; })()")
    pg.locator("#review").screenshot(path=str(SHOTS / "quote-copy-fallback.png"))
    flow_reqs += [r for r in pg.requests[start2:] if not (r["type"] == "image" and IMG_HOST in r["url"])]
    pg.context.close()
    ok = (status_before == "" and status == "Copied. Nothing has been sent." and clip == review
          and "Copied" not in st2 and "Nothing has been sent" in st2 and fb and sel and not flow_reqs)
    return ok, f"success: '{status}', clipboard matches summary={clip == review}; failure: fallback shown and selected={fb and sel}, no 'Copied' claim; network requests during quote flow: {len(flow_reqs)}"

@check("F12")
def f12(b):
    pg = new_page(b, 390, 844, reduced=True)
    t = ".menu-toggle"
    s0 = pg.get_attribute(t, "aria-expanded"); v0 = pg.is_visible('#primary-nav a[href="#range"]')
    pg.click(t); settle(pg, 100)
    s1 = pg.get_attribute(t, "aria-expanded"); v1 = pg.is_visible('#primary-nav a[href="#range"]')
    pg.screenshot(path=str(SHOTS / "mobile-menu-open.png"))
    pg.click('#primary-nav a[href="#materials"]'); settle(pg, 200)
    s2 = pg.get_attribute(t, "aria-expanded"); v2 = pg.is_visible('#primary-nav a[href="#range"]')
    pg.click(t); settle(pg, 100); pg.keyboard.press("Escape"); settle(pg, 100)
    s3 = pg.get_attribute(t, "aria-expanded"); focus = pg.evaluate("document.activeElement.classList.contains('menu-toggle')")
    pg.click(t); settle(pg, 100); pg.mouse.click(200, 700); settle(pg, 100)
    s4 = pg.get_attribute(t, "aria-expanded")
    pg.context.close()
    ok = s0 == "false" and not v0 and s1 == "true" and v1 and s2 == "false" and not v2 and s3 == "false" and focus and s4 == "false"
    return ok, f"closed->open->link closes->Escape closes (focus back {focus})->outside click closes: {[s0, s1, s2, s3, s4]}"

@check("F13")
def f13(b):
    pg = new_page(b, reduced=True)
    notes, ok = [], True
    for sec in ["range", "featured", "materials", "brands"]:
        pg.click(f'#primary-nav a[href="#{sec}"]'); settle(pg, 300)
        r = pg.evaluate(f"""() => {{ const h = document.querySelector('#{sec} h2'); const hb = document.querySelector('.site-header').getBoundingClientRect().bottom;
            const a = document.querySelector('#primary-nav a.is-active'); return {{ top: h.getBoundingClientRect().top, hb, active: a && a.getAttribute('href'), cur: a && a.getAttribute('aria-current') }}; }}""")
        good = r["top"] >= r["hb"] - 1 and r["active"] == f"#{sec}" and r["cur"] == "location"
        ok &= good; notes.append(f"{sec}: heading {round(r['top'] - r['hb'])}px below header, active {r['active']}")
    pg.click('#primary-nav a[href="#contact"]'); settle(pg, 300)
    contact_active = pg.evaluate("document.querySelector('#primary-nav a.is-active')?.getAttribute('href')")
    ok &= contact_active == "#contact"
    pg.evaluate("window.scrollTo(0,0)"); settle(pg, 200)
    none_at_top = pg.evaluate("document.querySelectorAll('#primary-nav a.is-active').length") == 0
    pg.context.close()
    return ok and none_at_top, "; ".join(notes) + f"; contact active={contact_active == '#contact'}; none active in hero={none_at_top}"

@check("F14")
def f14(b):
    pg = new_page(b, reduced=True)
    v0 = pg.evaluate("document.getElementById('to-top').classList.contains('is-visible')")
    pg.evaluate("window.scrollTo(0, 2500)"); settle(pg, 200)
    v1 = pg.evaluate("document.getElementById('to-top').classList.contains('is-visible')")
    pg.click("#to-top"); settle(pg, 400)
    y = pg.evaluate("scrollY")
    pg.context.close()
    return (not v0) and v1 and y == 0, f"hidden at top={not v0}, shown after hero={v1}, scrollY after click={y}"

@check("F15")
def f15(b):
    errors, page_errors = [], []
    for w, h in [(1280, 800), (390, 844), (320, 640)]:
        pg = new_page(b, w, h)
        scroll_through(pg); fill_full(pg); pg.click("#review-btn"); pg.click("#copy-btn"); settle(pg, 400)
        errors += [e for e in pg.console_errors if IMG_HOST not in e["url"] and "Failed to load resource" not in e["text"]]
        errors += [e for e in pg.console_errors if "Failed to load resource" in e["text"] and IMG_HOST not in e["url"] and e["url"]]
        page_errors += pg.page_errors
        pg.context.close()
    # no-JS
    pg = new_page(b, js=False, clipboard=False)
    nojs = pg.evaluate("""() => ({ cards: [...document.querySelectorAll('.range-card')].filter(c => c.offsetParent).length,
        h1: getComputedStyle(document.querySelector('.hero__title-inner')).opacity,
        details: document.querySelector('#kraissl-details .disclosure__content').getBoundingClientRect().height > 50,
        phone: document.body.innerText.includes('+971 6 566 4727'), email: document.body.innerText.includes('websales@pipelineproductsonline.com'),
        noscript: document.body.innerText.includes('The request sheet needs JavaScript'), form: !!document.querySelector('#quote-form').offsetParent,
        nav: !!document.querySelector('#primary-nav a').offsetParent })""")
    pg.screenshot(path=str(SHOTS / "no-javascript.png"), full_page=True)
    pg.context.close()
    nojs_ok = nojs["cards"] == 15 and nojs["h1"] == "1" and nojs["details"] and nojs["phone"] and nojs["email"] and nojs["noscript"] and not nojs["form"] and nojs["nav"]
    # keyboard only
    pg = new_page(b, reduced=True)
    def tab_to(sel, limit=80):
        for _ in range(limit):
            pg.keyboard.press("Tab")
            if pg.evaluate(f"document.activeElement.matches('{sel}')"): return True
        return False
    steps = []
    steps.append(tab_to("#item-y-ci .btn--add", 120)); pg.keyboard.press("Enter")
    steps.append(tab_to("#sheet-lines [data-k=size]", 200)); pg.keyboard.type("2")
    steps.append(tab_to('#sheet-lines [data-step="1"]', 6)); pg.keyboard.press("Enter")   # quantity + button
    steps.append(tab_to("#c-name")); pg.keyboard.type("Keyboard User")
    steps.append(tab_to("#c-contact")); pg.keyboard.type("kb@example.com")
    steps.append(tab_to("#review-btn")); pg.keyboard.press("Enter"); settle(pg, 100)
    steps.append(tab_to("#copy-btn")); pg.keyboard.press("Enter"); settle(pg, 300)
    kb = pg.text_content("#copy-status"); qty = pg.input_value("#sheet-lines [data-k=qty]")
    pg.context.close()
    kb_ok = all(steps) and kb == "Copied. Nothing has been sent." and qty == "2"
    ok = not errors and not page_errors and nojs_ok and kb_ok
    return ok, (f"console errors {len(errors)}, page errors {len(page_errors)} at 3 widths (external catalogue image failures excluded); "
                f"no-JS: {nojs}; keyboard-only quote completed={kb_ok} (qty via keyboard stepper={qty})")

def final_screenshots(b):
    for w, h, name in [(1280, 800, "desktop"), (390, 844, "mobile")]:
        pg = new_page(b, w, h)
        scroll_through(pg); settle(pg, 600)
        pg.screenshot(path=str(SHOTS / f"{name}-full.png"), full_page=True)
        pg.screenshot(path=str(SHOTS / f"{name}-first-view.png"))
        pg.context.close()

TITLES = {}
def load_titles():
    for line in (ROOT / "CRITERIA.md").read_text().splitlines():
        m = re.match(r"\| (A\d+|F\d+) \| (.+?) \|", line)
        if m: TITLES[m.group(1)] = m.group(2)

def write_report(images_note):
    load_titles()
    a = [k for k in results if k.startswith("A")]; f = [k for k in results if k.startswith("F")]
    passed = sum(1 for v in results.values() if v[0])
    out = ["# Test report", "", f"Run: {time.strftime('%Y-%m-%d %H:%M')} with Chromium (Playwright). Result: **{passed} of {len(results)} criteria passed.**", "", images_note, ""]
    for title, ids in [("Appeal, smoothness and finish", a), ("Functionality", f)]:
        out += [f"## {title}", "", "| ID | Result | Criterion | Evidence |", "|----|--------|-----------|----------|"]
        for k in ids:
            ok, d = results[k]
            out.append(f"| {k} | {'PASS' if ok else 'FAIL'} | {TITLES.get(k, '')} | {d.replace('|', '/')} |")
        out.append("")
    (ROOT / "TEST-REPORT.md").write_text("\n".join(out))
    return passed

if __name__ == "__main__":
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            checks = [a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15,
                      f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12, f13, f14, f15]
            only = sys.argv[1:]
            for c in checks:
                if not only or c.cid in only: c(browser)
            pg = new_page(browser); scroll_through(pg)
            loaded = pg.evaluate("[...document.querySelectorAll('img[data-fallback]')].filter(i=>i.naturalWidth>0).length")
            pg.context.close()
            if not only: final_screenshots(browser)
            browser.close()
        note = (f"Catalogue images: {loaded} of 6 loaded from pipelineproductsonline.com in this run."
                + ("" if loaded == 6 else " The rest could not be loaded in this run and showed the labelled placeholder, as the brief requires."))
        passed = write_report(note)
        print(f"\n{passed}/{len(results)} passed")
        sys.exit(0 if passed == len(results) else 1)
    finally:
        srv.terminate()
