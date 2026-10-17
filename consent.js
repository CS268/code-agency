(function () {
  var GA_ID = 'G-LYT113PWTZ';
  var KEY = 'cookieConsent';
  var TX = {
    fr: { text: "Nous utilisons Google Analytics pour mesurer l'audience, uniquement si vous acceptez.", ok: 'Accepter', no: 'Refuser', more: 'En savoir plus' },
    nl: { text: 'We gebruiken Google Analytics om het bezoek te meten, alleen als u akkoord gaat.', ok: 'Accepteren', no: 'Weigeren', more: 'Meer info' },
    en: { text: 'We use Google Analytics to measure audience, only if you accept.', ok: 'Accept', no: 'Decline', more: 'Learn more' }
  };
  var lang = (document.documentElement.lang || 'fr').slice(0, 2).toLowerCase();
  var t = TX[lang] || TX.fr;

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; }
  }
  function save(analytics) {
    try {
      localStorage.setItem(KEY, JSON.stringify({ necessary: true, analytics: analytics, marketing: analytics, date: new Date().toISOString() }));
    } catch (e) {}
  }
  function loadGA() {
    if (window.__gaLoaded) return;
    window.__gaLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.gtag('js', new Date());
    window.gtag('config', GA_ID);
  }
  function banner() {
    var b = document.createElement('div');
    b.setAttribute('role', 'dialog');
    b.setAttribute('aria-label', 'Cookies');
    b.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#0f172a;color:#e2e8f0;padding:14px 18px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:center;font:15px/1.5 system-ui,sans-serif;border-top:1px solid rgba(255,255,255,0.15)';
    var p = document.createElement('span');
    p.style.cssText = 'max-width:640px';
    p.textContent = t.text + ' ';
    var a = document.createElement('a');
    a.href = '/privacy-policy.html';
    a.textContent = t.more;
    a.style.cssText = 'color:#a5b4fc;text-decoration:underline';
    p.appendChild(a);
    function btn(label, primary, fn) {
      var x = document.createElement('button');
      x.type = 'button';
      x.textContent = label;
      x.style.cssText = 'min-height:40px;padding:8px 18px;border-radius:10px;font-weight:600;cursor:pointer;font-size:15px;border:1px solid #6366f1;' + (primary ? 'background:#6366f1;color:#fff' : 'background:transparent;color:#e2e8f0');
      x.onclick = fn;
      return x;
    }
    b.appendChild(p);
    b.appendChild(btn(t.no, false, function () { save(false); b.remove(); }));
    b.appendChild(btn(t.ok, true, function () { save(true); loadGA(); b.remove(); }));
    document.body.appendChild(b);
  }
  function start() {
    var c = read();
    if (c && c.analytics) { loadGA(); }
    if (!c) { banner(); }
  }
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', start); } else { start(); }
})();
