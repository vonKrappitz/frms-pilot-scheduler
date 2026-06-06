// Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
// SPDX-License-Identifier: Apache-2.0
// Headless wykonanie frms-web.html: shim DOM, klikamy każde okno, język i handlery.
const fs = require('fs');
const html = fs.readFileSync('frms-web.html', 'utf-8');

// --- shim DOM ---
function classList(){ const s=new Set(); return {
  add:(...c)=>c.forEach(x=>s.add(x)), remove:(...c)=>c.forEach(x=>s.delete(x)),
  toggle:(c)=>{ if(s.has(c)){s.delete(c);return false;} s.add(c); return true; },
  contains:(c)=>s.has(c) }; }
function makeEl(id){
  const el={ id:id||'', _html:'', style:{}, value:'', checked:false, textContent:'',
    classList:classList(), dataset:{}, children:[],
    setAttribute(){}, getAttribute(){return null;}, removeAttribute(){},
    appendChild(c){this.children.push(c);return c;}, removeChild(){},
    addEventListener(){}, removeEventListener(){}, remove(){},
    querySelector(){return null;}, querySelectorAll(){return [];},
    focus(){}, click(){}, insertAdjacentHTML(){}, getContext(){return {};} };
  Object.defineProperty(el,'innerHTML',{get(){return this._html;},set(v){this._html=String(v);}});
  return el;
}
const els={};
globalThis.document={ getElementById(id){return els[id]||(els[id]=makeEl(id));},
  querySelector(){return makeEl();}, querySelectorAll(){return [];},
  createElement(){return makeEl();}, addEventListener(){}, body:makeEl('body'),
  documentElement:makeEl('html') };
globalThis.window=globalThis;
globalThis.navigator={language:'pl'};
globalThis.setInterval=()=>0; globalThis.clearInterval=()=>{};
globalThis.setTimeout=()=>0; globalThis.clearTimeout=()=>{};
globalThis.requestAnimationFrame=()=>0;
globalThis.alert=()=>{}; globalThis.confirm=()=>true; globalThis.prompt=()=>'';
globalThis.localStorage={_d:{},getItem(k){return this._d[k]??null;},setItem(k,v){this._d[k]=String(v);},removeItem(k){delete this._d[k];}};
globalThis.__results=[];

// --- wyciągnięcie skryptów ---
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');

// --- driver dołączony do tej samej ewaluacji (dostęp do DANE i funkcji) ---
const driver = `
;(function(){
  function R(label, fn){ try{ fn(); __results.push([label,'ok']); } catch(e){ __results.push([label,'ERR: '+(e&&e.message?e.message:e)]); } }
  const FB = (typeof document!=='undefined')? document.createElement('button'):{classList:{add(){}, remove(){}}};
  // sekcje
  var sekcje=['dashboard','harmonogram','plan','piloci','alerty','sesje','symulator','law','awanse','mapa','serwis','centrum'];
  // render leaf w PL
  ['renderDashboard','renderHarmonogram','renderPlan','renderPiloci','renderAlerty','renderSesje','renderSymulator','renderLaw','renderAwanse','renderMapa','renderSerwis','renderCentrum'].forEach(function(fn){
    R('PL '+fn, function(){ if (typeof window[fn]==='function') window[fn](); });
  });
  R('PL renderAll', function(){ if(typeof renderAll==='function') renderAll(); });
  // przełączanie sekcji
  sekcje.forEach(function(n){ R('showSection '+n, function(){ showSection(n, FB); }); });
  // język EN
  R('setLang en', function(){ setLang('en', FB); });
  R('EN renderAll', function(){ renderAll(); });
  sekcje.forEach(function(n){ R('EN showSection '+n, function(){ showSection(n, FB); }); });
  R('setLang pl', function(){ setLang('pl', FB); });
  // nawigacja okien
  R('planNext x3', function(){ planNext(); planNext(); planNext(); });
  R('planPrev x5', function(){ planPrev(); planPrev(); planPrev(); planPrev(); planPrev(); });
  R('lawNext x3', function(){ lawNext(); lawNext(); lawNext(); });
  R('lawPrev x3', function(){ lawPrev(); lawPrev(); lawPrev(); });
  // wyprowadzenie argumentów z danych
  var plan = DANE.plan_15dni || [];
  var slotySwap=null, slotyTrain=null, slotyStol=null;
  for (var i=0;i<plan.length && (!slotySwap||!slotyTrain||!slotyStol);i++){
    var dz = plan[i]; var arr = (dz.sloty||dz);
    if (!Array.isArray(arr)) continue;
    for (var j=0;j<arr.length;j++){ var s=arr[j];
      if (!slotySwap && s.kandydaci_pic && s.kandydaci_pic.length) slotySwap={s:s,seat:'pic',pool:s.kandydaci_pic};
      if (!slotySwap && s.kandydaci_fo && s.kandydaci_fo.length) slotySwap={s:s,seat:'fo',pool:s.kandydaci_fo};
      if (!slotyTrain && s.fotel_szkoleniowy && s.fotel_szkoleniowy.length) slotyTrain=s;
      if (!slotyStol && s.kandydaci_stol_trudny && s.kandydaci_stol_trudny.length) slotyStol=s;
    }
  }
  // SWAP: rozwiń -> wybierz -> cofnij
  R('swap sekwencja', function(){
    if(!slotySwap){ __results.push(['swap','brak slotu z kandydatami (pomiń)']); return; }
    var key=slotySwap.s.id+'|'+slotySwap.seat;
    swapToggle(key); swapPick(key, slotySwap.pool[0].id); swapRevert(key);
  });
  // TRAIN: rozwiń -> wybierz -> cofnij
  R('train sekwencja', function(){
    if(!slotyTrain){ __results.push(['train','brak slotu szkoleniowego (pomiń)']); return; }
    trainExpandToggle(slotyTrain.id); trainPick(slotyTrain.id, slotyTrain.fotel_szkoleniowy[0].id); trainRevert(slotyTrain.id);
  });
  // STOL: włącz -> wybierz mentora -> cofnij -> wyłącz
  R('stol sekwencja', function(){
    if(!slotyStol){ __results.push(['stol','brak slotu STOL z obserwatorem (pomiń)']); return; }
    stolToggle(slotyStol.id); stolPick(slotyStol.id, slotyStol.kandydaci_stol_trudny[0].id); stolRevert(slotyStol.id); stolToggle(slotyStol.id);
  });
  // SERWIS: uzbrój -> potwierdź wezwanie -> uzbrój anulowanie -> potwierdź; oraz porzuć
  R('serwis pełny przepływ', function(){
    var sp = DANE.serwis_prognoza || [];
    var cand = sp.filter(function(x){ return !x.w_serwisie; });
    var id = cand.length ? cand[0].maszyna_id : (sp.length ? sp[0].maszyna_id : 'H1');
    serwArm(id,'wezwij'); serwPotwierdz(id,'wezwij');      // wezwana
    serwArm(id,'anuluj'); serwPotwierdz(id,'anuluj');      // anulowana
    serwArm(id,'wezwij'); serwPorzuc();                    // uzbrojone i porzucone
    serwWezwij(id);                                        // kompatybilność wstecz
  });
  // LAW: recurrent + recovery 5+5 na syntetycznym kluczu
  R('law recurrent', function(){ lawZaliczRecurrent('K1'); });
  R('law recovery 5+5', function(){ lawSetStarty('K2','5'); lawSetLadowania('K2','5'); lawZaliczRecovery('K2'); });
  R('law recovery 3+5 (za malo)', function(){ lawSetStarty('K3','3'); lawSetLadowania('K3','5'); lawZaliczRecovery('K3'); });
})();
`;

try { (0, eval)(scripts + '\n' + driver); }
catch(e){ globalThis.__results.push(['EVAL FATAL','ERR: '+(e&&e.message?e.message:e)]); }

let ok=0, err=0;
for (const [label, res] of globalThis.__results){
  if (String(res).startsWith('ERR')){ err++; console.log('  [FAIL] '+label+' -> '+res); }
  else ok++;
}
console.log(`\nWynik headless: ${ok} ok, ${err} błędów, kroków ${globalThis.__results.length}`);
// pokaż kilka pominięć/uwag
globalThis.__results.filter(([l,r])=>String(r).includes('pomiń')).forEach(([l,r])=>console.log('  [info] '+l+': '+r));
process.exit(err?1:0);
