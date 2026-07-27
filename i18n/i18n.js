/**
 * JCODE i18n — Lightweight translation engine (vanilla JS, zero deps, <3KB)
 * Language is stored in localStorage; switching translates DOM in-place.
 */
(function () {
  // Anti-FOUC: hide page until translations are applied
  document.documentElement.style.visibility = 'hidden';

  var CACHE_KEY = 'jcode_i18n_cache_v1';

  // Language detection: localStorage only, default 'fr'
  var lang = localStorage.getItem('jcode_lang') || 'fr';

  // Translation store
  var T = {};

  function t(key) {
    return (T[lang] && T[lang][key] !== undefined) ? T[lang][key] : null;
  }

  // Always fetch translations.json (FR included — switcher can change lang anytime)
  function load(cb) {
    var cached = localStorage.getItem(CACHE_KEY);
    if (cached) { try { T = JSON.parse(cached); } catch (e) { /* ignore */ } }

    fetch('i18n/translations.json')
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then(function (data) {
        // Support both flat {fr:{key:val}} and per-key {key:{fr:val}} structures
        if (data.fr && typeof data.fr === 'object' && !data.fr.en) {
          T = data; // flat structure
        } else {
          T = {}; // per-key structure — transform to flat
          Object.keys(data).forEach(function (key) {
            var val = data[key];
            if (val && typeof val === 'object') {
              Object.keys(val).forEach(function (lang) {
                if (!T[lang]) T[lang] = {};
                T[lang][key] = val[lang];
              });
            }
          });
        }
        try { localStorage.setItem(CACHE_KEY, JSON.stringify(data)); } catch (e) { /* quota */ }
        cb();
      })
      .catch(function () { cb(); }); // fall back to cached T
  }

  // Apply translations to DOM
  function apply() {
    document.documentElement.lang = lang;

    // SEO: title and meta description
    var titleEl = document.querySelector('title');
    if (titleEl) { var v = t('page.title'); if (v) titleEl.textContent = v; }
    var descEl = document.querySelector('meta[name="description"]');
    if (descEl) { var d = t('page.description'); if (d) descEl.setAttribute('content', d); }

    // [data-i18n="key"] → textContent
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var val = t(el.getAttribute('data-i18n'));
      if (val !== null) el.textContent = val;
    });

    // [data-i18n-html="key"] → innerHTML (rich content with tags)
    document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      var val = t(el.getAttribute('data-i18n-html'));
      if (val !== null) el.innerHTML = val;
    });

    // [data-i18n-attr="attrName:key,..."] → set attributes
    document.querySelectorAll('[data-i18n-attr]').forEach(function (el) {
      el.getAttribute('data-i18n-attr').split(',').forEach(function (pair) {
        var segs = pair.trim().split(':');
        if (segs.length === 2) {
          var val = t(segs[1].trim());
          if (val !== null) el.setAttribute(segs[0].trim(), val);
        }
      });
    });

    // Language switcher: highlight active + wire click handlers
    document.querySelectorAll('.lang-btn, .lang-switcher a').forEach(function (btn) {
      var bl = (btn.getAttribute('data-lang') || btn.textContent.trim()).toLowerCase();
      if (bl === lang) {
        btn.classList.add('active');
        btn.setAttribute('data-lang-active', lang);
        btn.style.cssText = 'padding:0.4rem 1rem;border-radius:50px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:var(--primary-light);font-weight:600;font-size:0.8rem;text-decoration:none;transition:all 0.3s';
      } else {
        btn.classList.remove('active');
        btn.removeAttribute('data-lang-active');
        btn.style.cssText = 'padding:0.4rem 1rem;border-radius:50px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:var(--gray-light);font-weight:600;font-size:0.8rem;text-decoration:none;transition:all 0.3s';
      }
      btn.onclick = function (e) {
        e.preventDefault();
        if (bl !== lang) setLanguage(bl);
      };
    });

    // Reveal page
    document.documentElement.style.visibility = '';
  }

  // Public API: switch language in-place (no reload)
  window.setLanguage = function (newLang) {
    lang = newLang;
    localStorage.setItem('jcode_lang', newLang);
    apply();
  };

  // Init on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function () {
    load(apply);
  });
})();
