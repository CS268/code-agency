# GATES — pages nl/ et en/ synchronisées avec le revamp FR

- [ ] G1 Les clés nl/en sont identiques à la racine
  CHECK: node scripts/verify-lang-pages.mjs keys
  EXPECT: keys verification passed

- [ ] G2 Aucun texte français visible dans nl/ ni en/ (cible 0)
  CHECK: node scripts/verify-lang-pages.mjs french-leak
  EXPECT: french-leak verification passed

- [ ] G3 Le bon bouton de langue est actif
  CHECK: node scripts/verify-lang-pages.mjs lang-active
  EXPECT: lang-active verification passed

- [ ] G4 Grille, CSS et liens internes
  CHECK: node scripts/verify-lang-pages.mjs grid && node scripts/verify-lang-pages.mjs css && node scripts/verify-lang-pages.mjs links
  EXPECT: links verification passed

- [ ] G5 Structure saine des 3 site-web.html
  CHECK: node -e "const fs=require('fs');for(const f of ['site-web.html','en/site-web.html','nl/site-web.html']){const s=fs.readFileSync(f,'utf8');const n=t=>s.split(t).length-1;if(n('<body')!==1||n('</body>')!==1||n('id=\"offre\"')!==1)throw new Error(f)}console.log('SITEWEB OK')"
  EXPECT: SITEWEB OK

- [ ] G6 (manuel) Les 10 clés modifiées vs HEAD (fin promo 37€) sont voulues, prix Teaser 399€ confirmé
  MANUAL: preuve = diff relu et prix confirmé par le propriétaire

- [ ] G7 Pas d'attribut français dans les site-web en/nl (aria-label, title du quiz)
  CHECK: node -e "const fs=require('fs');for(const f of ['en/site-web.html','nl/site-web.html']){if(fs.readFileSync(f,'utf8').includes('Quiz de recommandation'))throw new Error(f)}console.log('QUIZ ATTR OK')"
  EXPECT: QUIZ ATTR OK

- [ ] G8 Plus aucune trace de la promo 37€ / PROMO460 dans les pages et les traductions
  CHECK: node -e "const fs=require('fs');const bad=[];for(const f of ['index.html','en/index.html','nl/index.html','site-web.html','en/site-web.html','nl/site-web.html']){if(/PROMO460|37 ?€/.test(fs.readFileSync(f,'utf8')))bad.push(f)}if(bad.length)throw new Error(bad.join(', '));console.log('PROMO CLEAN')"
  EXPECT: PROMO CLEAN

- [ ] G9 (manuel) Décision prise sur promo-septembre (supprimée ou redirigée), terms.html, merci.html et les 2 clés mortes
  MANUAL: preuve = décision notée par le propriétaire
