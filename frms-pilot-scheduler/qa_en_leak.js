// Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
// SPDX-License-Identifier: Apache-2.0
// Skan przecieków polskiego UI w trybie EN. Renderuje każdą sekcję po EN i szuka
// polskich słów, które nie powinny się pojawić (pomija nazwy własne i kody).
const fs=require('fs');
const html=fs.readFileSync('frms-web.html','utf-8');
function cl(){const s=new Set();return{add:(...c)=>c.forEach(x=>s.add(x)),remove:(...c)=>c.forEach(x=>s.delete(x)),toggle:c=>{if(s.has(c)){s.delete(c);return false}s.add(c);return true},contains:c=>s.has(c)};}
function el(id){const e={id:id||'',_html:'',style:{},value:'',checked:false,textContent:'',classList:cl(),dataset:{},children:[],setAttribute(){},getAttribute(){return null},appendChild(c){this.children.push(c);return c},addEventListener(){},removeEventListener(){},remove(){},querySelector(){return null},querySelectorAll(){return[]},focus(){},getContext(){return{}}};Object.defineProperty(e,'innerHTML',{get(){return this._html},set(v){this._html=String(v)}});return e;}
const els={};
globalThis.document={getElementById(id){return els[id]||(els[id]=el(id))},querySelector(){return el()},querySelectorAll(){return[]},createElement(){return el()},addEventListener(){},body:el('body')};
globalThis.window=globalThis; globalThis.setInterval=()=>0; globalThis.clearInterval=()=>{}; globalThis.setTimeout=()=>0; globalThis.requestAnimationFrame=()=>0;
globalThis.alert=()=>{}; globalThis.localStorage={_d:{},getItem(k){return this._d[k]??null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}};
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
globalThis.__sekcje=['dashboard','harmonogram','plan','piloci','alerty','sesje','symulator','law','awanse','mapa','serwis','centrum'];
const driver=`;(function(){ setLang('en', document.createElement('button')); renderAll(); })();`;
try{(0,eval)(scripts+'\n'+driver);}catch(e){console.log('EVAL ERR',e.message);process.exit(2);}

// polskie słowa UI, które w EN nie powinny wystąpić (granice słów)
const PL=['\\bdni\\b','\\bgodzin','\\bbez lotu','\\btermin','priorytet','\\bpowód','\\btrudne','scenariusze','autorotacje','awarie','lądowania','wezwanie','wezwana','Maszyna','\\bBrak\\b','w serwisie','pobieżny','poważny','\\bremont','recurrent kwartalny','\\bdo przeglądu','\\bNalot\\b','Miejsce','Akcja','\\bDni\\b','\\bWYSOKI\\b','\\bNISKI\\b','\\bSREDNI\\b','POBIEZNY'];
const rx=new RegExp('('+PL.join('|')+')','g');
let total=0;
for(const name of globalThis.__sekcje){
  const cont=els[name+'-content']||els['cards-kadra']; // sekcje piszą do <name>-content
  const html2=(els[name+'-content']||{})._html||'';
  const m=html2.match(rx);
  if(m){ const uniq=[...new Set(m)]; total+=uniq.length; console.log(`[PL w EN] ${name}: ${uniq.join(', ')}`); }
}
// dashboard pisze do cards-*; sprawdź je osobno
['cards-kadra','cards-operacje','cards-law'].forEach(id=>{ const h=(els[id]||{})._html||''; const m=h.match(rx); if(m){const u=[...new Set(m)];total+=u.length;console.log(`[PL w EN] ${id}: ${u.join(', ')}`);} });
console.log(total? `\nZNALEZIONO przecieki PL w EN: ${total}` : '\nBrak przecieków PL w EN (czysto).');
process.exit(total?1:0);
