# Copyright 2026 Maciej M. Kasperek ("vonKrappitz")
# SPDX-License-Identifier: Apache-2.0
"""
Generator statycznego interfejsu webowego FRMS (frms-web.html).

Dane wstrzykiwane są przez UNIKALNY znacznik `__DANE__` zwykłym podstawieniem
tekstu (str.replace, count=1), nigdy regexem. To eliminuje pułapkę zachłannego
`const DANE = {.*};`, która zjadała funkcje renderujące. Regeneracja: po prostu
uruchom ten moduł, zawsze produkuje spójny plik.
"""

import json
from pathlib import Path

from frms.export_json import eksport_do_json

ZNACZNIK = "__DANE__"

SZABLON = r"""<!DOCTYPE html>
<!-- FRMS pilot scheduler (KPRL/LPR). Copyright 2026 Maciej M. Kasperek ("vonKrappitz"). SPDX-License-Identifier: Apache-2.0 -->
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FRMS — System planowania pilotów ratownictwa lotniczego</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background: #f5f6f8; color: #1a1a1a; font-size: 14px; }
header { background: linear-gradient(135deg, #1a3a5c 0%, #2c5282 100%); color: white; padding: 16px 0; }
header .container { display: flex; justify-content: space-between; align-items: center; }
header h1 { font-size: 20px; font-weight: 600; }
header .subtitle { font-size: 12px; opacity: 0.85; margin-top: 4px; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
.lang-switch { display: flex; gap: 4px; }
.lang-btn { background: rgba(255,255,255,0.15); color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: 500; }
.lang-btn:hover { background: rgba(255,255,255,0.25); }
.lang-btn.active { background: white; color: #1a3a5c; }
nav { background: white; border-bottom: 1px solid #e2e6ea; position: sticky; top: 0; z-index: 10; }
nav .container { display: flex; flex-wrap: wrap; }
.nav-btn { background: none; border: none; border-bottom: 3px solid transparent; padding: 14px 16px; font-size: 14px; color: #555; cursor: pointer; font-weight: 500; }
.nav-btn:hover { color: #1a3a5c; background: #f5f6f8; }
.nav-btn.active { color: #1a3a5c; border-bottom-color: #c8102e; font-weight: 600; }
main { padding: 24px 0; }
main .container { }
.section { display: none; }
.section.active { display: block; animation: fadeIn 0.3s; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
h2 { color: #1a3a5c; margin-bottom: 16px; font-size: 22px; font-weight: 600; }
h3 { color: #2c5282; margin: 20px 0 12px; font-size: 16px; font-weight: 600; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: white; border-left: 4px solid #2c5282; border-radius: 6px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card .label { color: #6b7280; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }
.card .value { color: #1a3a5c; font-size: 28px; font-weight: 700; margin-top: 6px; }
.card .sublabel { color: #9ca3af; font-size: 12px; margin-top: 4px; }
.card.alert { border-left-color: #c8102e; } .card.alert .value { color: #c8102e; }
.card.success { border-left-color: #16a34a; } .card.success .value { color: #16a34a; }
.panel { background: white; border-radius: 6px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #f5f6f8; color: #1a3a5c; text-align: left; padding: 10px 12px; font-weight: 600; border-bottom: 2px solid #e2e6ea; }
td { padding: 10px 12px; border-bottom: 1px solid #eef1f4; }
tr:hover td { background: #fafbfc; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600; background: #eef1f4; color: #374151; }
.badge-A { background: #e0f2fe; color: #075985; }
.badge-B { background: #dcfce7; color: #166534; }
.badge-C { background: #fef3c7; color: #92400e; }
.badge-D { background: #fee2e2; color: #991b1b; }
.badge-recurrent { background: #dbeafe; color: #1e40af; }
.badge-recovery { background: #fee2e2; color: #991b1b; }
.nav-day { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.nav-day button { background: #1a3a5c; color: white; border: none; border-radius: 4px; padding: 8px 14px; cursor: pointer; font-size: 16px; }
.nav-day button:disabled { background: #cbd5e1; cursor: default; }
.banner { margin-bottom: 16px; padding: 12px 16px; border-radius: 4px; }
.banner.ok { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
.banner.warn { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.muted { color: #6b7280; margin-bottom: 12px; }
</style>
</head>
<body>
<header>
    <div class="container">
        <div>
            <h1>FRMS</h1>
            <div class="subtitle" data-pl="System planowania pilotów ratownictwa lotniczego (KPRL/LPR)" data-en="Air rescue pilot scheduling system (KPRL/LPR)">System planowania pilotów ratownictwa lotniczego (KPRL/LPR)</div>
        </div>
        <div class="lang-switch">
            <button class="lang-btn active" onclick="setLang('pl', this)">PL</button>
            <button class="lang-btn" onclick="setLang('en', this)">EN</button>
        </div>
    </div>
</header>

<nav><div class="container">
    <button class="nav-btn active" onclick="showSection('dashboard', this)" data-pl="Dashboard" data-en="Dashboard">Dashboard</button>
    <button class="nav-btn" onclick="showSection('harmonogram', this)" data-pl="Harmonogram" data-en="Schedule">Harmonogram</button>
    <button class="nav-btn" onclick="showSection('plan', this)" data-pl="Plan 15 dni" data-en="15-day plan">Plan 15 dni</button>
    <button class="nav-btn" onclick="showSection('piloci', this)" data-pl="Piloci" data-en="Pilots">Piloci</button>
    <button class="nav-btn" onclick="showSection('alerty', this)" data-pl="Alerty" data-en="Alerts">Alerty</button>
    <button class="nav-btn" onclick="showSection('sesje', this)" data-pl="Sesje LAW" data-en="LAW Sessions">Sesje LAW</button>
    <button class="nav-btn" onclick="showSection('symulator', this)" data-pl="Symulator EPDE" data-en="EPDE Simulator">Symulator EPDE</button>
    <button class="nav-btn" onclick="showSection('law', this)" data-pl="Grafik LAW" data-en="LAW Schedule">Grafik LAW</button>
    <button class="nav-btn" onclick="showSection('awanse', this)" data-pl="Awanse" data-en="Promotions">Awanse</button>
    <button class="nav-btn" onclick="showSection('mapa', this)" data-pl="Sieć / Sektory" data-en="Network / Sectors">Sieć / Sektory</button>
    <button class="nav-btn" onclick="showSection('serwis', this)" data-pl="Serwis" data-en="Maintenance">Serwis</button>
    <button class="nav-btn" onclick="showSection('centrum', this)" data-pl="Centrum (live)" data-en="Ops Centre (live)">Centrum (live)</button>
</div></nav>

<main><div class="container">

<section id="dashboard" class="section active">
    <h2 data-pl="Dashboard operacyjny" data-en="Operational Dashboard">Dashboard operacyjny</h2>
    <h3 data-pl="Kadra" data-en="Personnel">Kadra</h3>
    <div class="cards" id="cards-kadra"></div>
    <h3 data-pl="Operacje" data-en="Operations">Operacje</h3>
    <div class="cards" id="cards-operacje"></div>
    <h3 data-pl="Symulator LAW Dęblin" data-en="LAW Dęblin Simulator">Symulator LAW Dęblin</h3>
    <div class="cards" id="cards-law"></div>
</section>

<section id="harmonogram" class="section">
    <h2 data-pl="Harmonogram tygodniowy" data-en="Weekly Schedule">Harmonogram tygodniowy</h2>
    <div class="panel" id="harmonogram-content"></div>
</section>

<section id="plan" class="section">
    <h2 data-pl="Plan operacyjny — 15 dni" data-en="Operational plan — 15 days">Plan operacyjny — 15 dni</h2>
    <p class="muted" data-pl="Dziś i kolejne 14 dni. Przewijaj dzień po dniu." data-en="Today and the next 14 days. Step day by day.">Dziś i kolejne 14 dni. Przewijaj dzień po dniu.</p>
    <div class="nav-day">
        <button id="plan-prev" onclick="planPrev()">&#9664;</button>
        <div style="min-width:260px; text-align:center;">
            <strong id="plan-data" style="font-size:1.1em;"></strong>
            <div style="color:#9ca3af; font-size:0.9em;"><span id="plan-pozycja"></span> &middot; <span id="plan-podsumowanie"></span></div>
        </div>
        <button id="plan-next" onclick="planNext()">&#9654;</button>
    </div>
    <div class="panel" id="plan-content"></div>
</section>

<section id="piloci" class="section">
    <h2 data-pl="Lista pilotów" data-en="Pilot Roster">Lista pilotów</h2>
    <div class="panel" id="piloci-content"></div>
</section>

<section id="alerty" class="section">
    <h2 data-pl="Alerty operacyjne" data-en="Operational Alerts">Alerty operacyjne</h2>
    <div class="panel" id="alerty-content"></div>
</section>

<section id="sesje" class="section">
    <h2 data-pl="Sesje symulatorowe LAW Dęblin (EPDE)" data-en="Simulator Sessions — LAW Dęblin (EPDE)">Sesje symulatorowe LAW Dęblin (EPDE)</h2>
    <p class="muted" data-pl="Recurrent kwartalny: 2 dni × 12h, trudne scenariusze. Recovery: helikoptery 21 dni / samolot 45 dni bez lotu, sesja 1 dzień × 6h, okno 45 dni." data-en="Quarterly recurrent: 2 days × 12h. Recovery: helicopters 21 days / airplane 45 days without flight, 1-day × 6h session, 45-day window.">Recurrent kwartalny: 2 dni × 12h, trudne scenariusze. Recovery: helikoptery 21 dni / samolot 45 dni bez lotu, sesja 1 dzień × 6h, okno 45 dni.</p>
    <div class="panel" id="sesje-content"></div>
</section>

<section id="symulator" class="section">
    <h2 data-pl="Symulator EPDE — obłożenie i pojemność" data-en="EPDE Simulator — occupancy and capacity">Symulator EPDE — obłożenie i pojemność</h2>
    <p class="muted" data-pl="Jeden egzemplarz na klasę, jeden pilot na dzień. Kolizje przesuwane w oknie: recurrent w kwartale, recovery w 45 dniach. Czego nie da się zmieścić, trafia do przepełnienia." data-en="One unit per class, one pilot per day. Collisions shifted within the window. What does not fit goes to overflow.">Jeden egzemplarz na klasę, jeden pilot na dzień. Kolizje przesuwane w oknie: recurrent w kwartale, recovery w 45 dniach. Czego nie da się zmieścić, trafia do przepełnienia.</p>
    <div id="symulator-banner"></div>
    <div class="panel" id="symulator-content"></div>
    <div id="symulator-nieobsadzone"></div>
</section>

<section id="law" class="section">
    <h2 data-pl="Grafik treningów LAW Dęblin" data-en="LAW Dęblin Training Schedule">Grafik treningów LAW Dęblin</h2>
    <p class="muted" data-pl="Zaplanowane sesje na dziś i kolejne 14 dni. Recovery zalicza się od 5 startów i lądowań, recurrent jednym przyciskiem." data-en="Planned sessions for today and the next 14 days. Recovery passes from 5 takeoffs and landings, recurrent with one button.">Zaplanowane sesje na dziś i kolejne 14 dni. Recovery zalicza się od 5 startów i lądowań, recurrent jednym przyciskiem.</p>
    <div class="nav-day">
        <button id="law-prev" onclick="lawPrev()">&#9664;</button>
        <div style="min-width:260px; text-align:center;">
            <strong id="law-data" style="font-size:1.1em;"></strong>
            <div style="color:#9ca3af; font-size:0.9em;"><span id="law-pozycja"></span> &middot; <span id="law-liczba"></span></div>
        </div>
        <button id="law-next" onclick="lawNext()">&#9654;</button>
    </div>
    <div class="panel" id="law-content"></div>
</section>
<section id="awanse" class="section">
    <h2 data-pl="Kandydaci do awansu" data-en="Promotion candidates">Kandydaci do awansu</h2>
    <p class="muted" data-pl="Brak automatycznego awansu. Awans wymaga kompletu kryteriów i zatwierdzenia przez minimum 3 instruktorów kat D ze wspólną historią lotów. Progi nalotu robocze." data-en="No automatic promotion. Requires all criteria and approval by at least 3 category-D instructors with shared flight history. Hour thresholds are provisional.">Brak automatycznego awansu. Awans wymaga kompletu kryteriów i zatwierdzenia przez minimum 3 instruktorów kat D ze wspólną historią lotów. Progi nalotu robocze.</p>
    <div class="panel" id="awanse-content"></div>
</section>
<section id="mapa" class="section">
    <h2 data-pl="Sieć ratownictwa lotniczego — sektory" data-en="Air rescue network — sectors">Sieć ratownictwa lotniczego — sektory</h2>
    <p class="muted" data-pl="Schemat sieci po reformie. Węzły CRL jako przesiadki, bazy podpięte liniami sektorów." data-en="Post-reform network schematic. CRL hubs as interchanges, bases connected by sector lines.">Schemat sieci po reformie. Węzły CRL jako przesiadki, bazy podpięte liniami sektorów.</p>
    <div class="panel" id="mapa-content"></div>
</section>
<section id="serwis" class="section">
    <h2 data-pl="Serwis floty — prognoza i wezwania" data-en="Fleet maintenance — forecast and recalls">Serwis floty — prognoza i wezwania</h2>
    <p class="muted" data-pl="Nalot pozostały do najbliższego progu (pobieżny 100 h, poważny 600 h, remont 3000 h) i dni przy założonym tempie nalotu. Egzemplarze blisko progu trafiają do wezwań priorytetowych." data-en="Hours remaining to the nearest threshold (light 100 h, heavy 600 h, overhaul 3000 h) and days at assumed usage. Aircraft near threshold are flagged for priority recall.">Nalot pozostały do najbliższego progu (pobieżny 100 h, poważny 600 h, remont 3000 h) i dni przy założonym tempie nalotu. Egzemplarze blisko progu trafiają do wezwań priorytetowych.</p>
    <div id="serwis-content"></div>
</section>
<section id="centrum" class="section">
    <h2 data-pl="Centrum dowodzenia — mapa live" data-en="Operations centre — live map">Centrum dowodzenia — mapa live</h2>
    <p class="muted" data-pl="Sytuacja floty z telemetrii. Źródło: adapter MockTelemetry (zaślepka portu); realne GPS podmienia tylko adapter." data-en="Fleet situation from telemetry. Source: MockTelemetry adapter (port stub); real GPS swaps only the adapter.">Sytuacja floty z telemetrii. Źródło: adapter MockTelemetry (zaślepka portu); realne GPS podmienia tylko adapter.</p>
    <div id="centrum-content"></div>
</section>

</div></main>

<script>
const DANE = __DANE__;
let currentLang = 'pl';
const TXT = {
    pl: {recurrent:'Recurrent', recovery:'Recovery', dni:'dni', godzin:'godz', filled:'obsadzonych', unfilled:'nieobsadzony', date:'Data', base:'Baza', duty:'Typ dyżuru', klasa:'Klasa', min:'Min', crew:'Obsada', machine:'Maszyna', pilot:'Pilot', kat:'Kategoria', ratings:'Type ratingi', ready:'Gotowy', overload:'Przeciążony', type:'Typ', reason:'Powód', time:'Czas', window:'Okno', sims:'Symulatory zajęte', tak:'tak', nie:'nie', nalot:'Nalot na modelu', rejestracja:'Rejestracja', zalicz:'Zalicz', zaliczono:'Zaliczono', starty:'Starty i lądowania', termin:'Termin', brakSesji:'Brak sesji tego dnia', sesje:'sesji', wybierz:'Wybierz', zmieniony:'zmieniony', cofnij:'cofnij', kandydaci:'Kandydaci do zamiany', brakKand:'brak kandydatów', szkoleniowy:'szkoleniowy', nadzor:'nadzór', kursy:'Kursy', wolne:'Wolne', brakKursu:'brak kursu', kursAlertNag:'Braki kursów (obsadzeni piloci)'},
    en: {recurrent:'Recurrent', recovery:'Recovery', dni:'days', godzin:'h', filled:'filled', unfilled:'unfilled', date:'Date', base:'Base', duty:'Duty', klasa:'Class', min:'Min', crew:'Crew', machine:'Aircraft', pilot:'Pilot', kat:'Category', ratings:'Type ratings', ready:'Ready', overload:'Overloaded', type:'Type', reason:'Reason', time:'Duration', window:'Window', sims:'Simulators in use', tak:'yes', nie:'no', nalot:'Hours on model', rejestracja:'Record', zalicz:'Pass', zaliczono:'Passed', starty:'Takeoffs and landings', termin:'Deadline', brakSesji:'No sessions this day', sesje:'sessions', wybierz:'Choose', zmieniony:'changed', cofnij:'undo', kandydaci:'Replacement candidates', brakKand:'no candidates', szkoleniowy:'training', nadzor:'supervisor', kursy:'Courses', wolne:'Off', brakKursu:'missing course', kursAlertNag:'Missing courses (assigned pilots)'}
};
function t(k){ return TXT[currentLang][k] || k; }

function setLang(lang, btn){
    currentLang = lang;
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    document.querySelectorAll('[data-pl]').forEach(el => { el.textContent = el.dataset[lang] || el.textContent; });
    renderAll();
}
function showSection(name, btn){
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(name).classList.add('active');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
}
function card(label, value, sublabel, cls){
    return `<div class="card ${cls||''}"><div class="label">${label}</div><div class="value">${value}</div>${sublabel?`<div class="sublabel">${sublabel}</div>`:''}</div>`;
}
function osoba(o){ return o ? `${o.imie} ${o.nazwisko} <span class="badge badge-${o.kategoria}">${o.kategoria}</span>` : ''; }

const PIDX = {};
(DANE.piloci || []).forEach(p => PIDX[p.id] = p);
function osobaId(id){ const p = PIDX[id]; return p ? osoba(p) : id; }

const swapStan = {};     // klucz slotId|seat -> nowy pilot_id
const expandStan = {};   // klucz slotId|seat -> bool (rozwinięta pula)
function swapToggle(key){ expandStan[key] = !expandStan[key]; renderPlan(); }
function swapPick(key, id){ swapStan[key] = id; expandStan[key] = false; renderPlan(); }
function swapRevert(key){ delete swapStan[key]; renderPlan(); }

function seatCell(slot, seat){
    const orig = seat === 'pic' ? slot.pic : slot.fo;
    if (!orig) return `<span style="color:#9ca3af;">—</span>`;
    const pool = (seat === 'pic' ? slot.kandydaci_pic : slot.kandydaci_fo) || [];
    const key = slot.id + '|' + seat;
    const curId = swapStan[key] || orig.id;
    const rola = seat === 'pic' ? 'PIC' : (currentLang === 'pl' ? '2. pilot' : 'FO');
    const nazwa = osobaId(curId);
    // jawny przycisk zmiany pilota; czytelny, widoczny zawsze gdy fotel obsadzony
    const zmienTxt = currentLang === 'pl' ? (expandStan[key] ? 'zwiń' : 'zmień') : (expandStan[key] ? 'close' : 'change');
    const zmien = `<a onclick="swapToggle('${key}')" style="cursor:pointer;color:#1a3a5c;text-decoration:underline;font-size:11px;margin-left:6px;">&#9998; ${zmienTxt}</a>`;
    let extra = '';
    if (swapStan[key]){
        extra = ` <span class="badge badge-recovery">${t('zmieniony')}</span> <a onclick="swapRevert('${key}')" style="cursor:pointer;color:#c8102e;text-decoration:underline;">${t('cofnij')}</a>`;
    }
    let lista = '';
    if (expandStan[key]){
        if (pool.length){
            lista = `<div style="margin-top:8px;padding:8px;background:#f5f6f8;border-radius:4px;"><div style="font-size:11px;color:#6b7280;margin-bottom:6px;">${t('kandydaci')}</div>`;
            pool.forEach(c => {
                const szk = c.szk ? ` <span class="badge badge-recovery">${t('szkoleniowy')}</span>${c.nadz ? ' <span style="font-size:11px;color:#6b7280;">'+t('nadzor')+': '+osobaId(c.nadz)+'</span>' : ''}` : '';
                lista += `<div style="margin:3px 0;"><button onclick="swapPick('${key}','${c.id}')" style="background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;font-size:12px;">${t('wybierz')}</button> ${osobaId(c.id)}${szk}</div>`;
            });
            lista += '</div>';
        } else {
            lista = `<div style="margin-top:6px;font-size:12px;color:#9ca3af;">${t('brakKand')}</div>`;
        }
    }
    return `<div><span style="font-size:11px;color:#9ca3af;">${rola}:</span> ${nazwa}${swapStan[key]?'':zmien}${extra}</div>${lista}`;
}

const BTNS = "background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;font-size:12px;";
const trainStan = {}, trainExpand = {}, stolOn = {}, stolPilot = {};
function trainExpandToggle(k){ trainExpand[k] = !trainExpand[k]; renderPlan(); }
function trainPick(k, id){ trainStan[k] = id; trainExpand[k] = false; renderPlan(); }
function trainRevert(k){ delete trainStan[k]; renderPlan(); }
function stolToggle(k){ stolOn[k] = !stolOn[k]; if (!stolOn[k]) delete stolPilot[k]; renderPlan(); }
function stolPick(k, id){ stolPilot[k] = id; renderPlan(); }
function stolRevert(k){ delete stolPilot[k]; renderPlan(); }

function dodatkoweFotele(s){
    const pl = currentLang === 'pl';
    let h = '';
    if (s.fotel_szkoleniowy && s.fotel_szkoleniowy.length){
        const k = s.id;
        if (trainStan[k]){
            const c = s.fotel_szkoleniowy.find(x => x.id === trainStan[k]) || {};
            const nadz = c.nadz ? ` <span style="font-size:11px;color:#6b7280;">${t('nadzor')}: ${osobaId(c.nadz)}</span>` : '';
            h += `<div style="margin-top:6px;"><span class="badge badge-recovery">${t('szkoleniowy')}</span> ${osobaId(trainStan[k])}${nadz} <a onclick="trainRevert('${k}')" style="cursor:pointer;color:#c8102e;text-decoration:underline;">${t('cofnij')}</a></div>`;
        } else {
            h += `<div style="margin-top:6px;"><a onclick="trainExpandToggle('${k}')" style="cursor:pointer;color:#1a3a5c;text-decoration:underline;font-size:12px;">+ ${pl?'fotel szkoleniowy':'training seat'}</a></div>`;
            if (trainExpand[k]){
                h += `<div style="margin-top:6px;padding:8px;background:#f5f6f8;border-radius:4px;">`;
                s.fotel_szkoleniowy.forEach(c => { h += `<div style="margin:3px 0;"><button onclick="trainPick('${k}','${c.id}')" style="${BTNS}">${t('wybierz')}</button> ${osobaId(c.id)}</div>`; });
                h += `</div>`;
            }
        }
    }
    if (s.kandydaci_stol_trudny && s.kandydaci_stol_trudny.length){
        const k = s.id, on = !!stolOn[k];
        h += `<div style="margin-top:6px;"><label style="font-size:12px;cursor:pointer;"><input type="checkbox" ${on?'checked':''} onchange="stolToggle('${k}')"> ${pl?'trudne warunki (mentor/obserwator)':'difficult conditions (mentor/observer)'}</label></div>`;
        if (on){
            if (stolPilot[k]){
                h += `<div style="margin-top:4px;"><span style="font-size:11px;color:#9ca3af;">${pl?'mentor/obserwator:':'mentor/observer:'}</span> ${osobaId(stolPilot[k])} <a onclick="stolRevert('${k}')" style="cursor:pointer;color:#c8102e;text-decoration:underline;">${t('cofnij')}</a> <span style="font-size:10px;color:#9ca3af;">${pl?'(kapitanem pozostaje kat A)':'(category A remains captain)'}</span></div>`;
            } else {
                h += `<div style="margin-top:4px;padding:8px;background:#f5f6f8;border-radius:4px;">`;
                h += `<div style="font-size:10px;color:#9ca3af;margin-bottom:4px;">${pl?'prywatna biegłość STOL, dodatkowa niepilotująca załoga, nie copilot':'private STOL proficiency, additional non-piloting crew, not a co-pilot'}</div>`;
                s.kandydaci_stol_trudny.forEach(c => { const rb = c.rola==='mentor' ? `<span class="badge badge-D">mentor</span>` : `<span class="badge badge-C">${pl?'wsparcie':'support'}</span>`; h += `<div style="margin:3px 0;"><button onclick="stolPick('${k}','${c.id}')" style="${BTNS}">${t('wybierz')}</button> ${osobaId(c.id)} ${rb}</div>`; });
                h += `</div>`;
            }
        }
    }
    return h;
}

function planTabela(sloty){
    let h = `<table><thead><tr><th>${t('base')}</th><th>${t('duty')}</th><th>${t('klasa')}</th><th>${t('min')}</th><th>${t('crew')}</th></tr></thead><tbody>`;
    sloty.forEach(s => {
        let crew = seatCell(s, 'pic');
        if (s.fo) crew += seatCell(s, 'fo');
        if (s.instruktor) crew += `<div><span style="font-size:11px;color:#9ca3af;">${currentLang==='pl'?'instruktor':'instructor'}:</span> ${osoba(s.instruktor)}</div>`;
        crew += dodatkoweFotele(s);
        h += `<tr><td>${s.baza_id}</td><td>${s.typ_dyzuru}</td><td><span class="badge">${s.wymagana_klasa}</span></td><td><span class="badge badge-${s.wymagana_kategoria_min}">${s.wymagana_kategoria_min}</span></td><td>${crew}</td></tr>`;
    });
    return h + '</tbody></table>';
}

function renderDashboard(){
    const s = DANE.statystyki, pl = currentLang==='pl';
    document.getElementById('cards-kadra').innerHTML =
        card(pl?'Piloci':'Pilots', s.liczba_pilotow) +
        card('A / B / C / D', s.rozklad_kategorii.A+' / '+s.rozklad_kategorii.B+' / '+s.rozklad_kategorii.C+' / '+s.rozklad_kategorii.D) +
        card(pl?'Bazy':'Bases', s.liczba_baz);
    document.getElementById('cards-operacje').innerHTML =
        card(pl?'Sloty operacyjne':'Operational slots', s.liczba_slotow_operacyjnych) +
        card(pl?'Obsadzenie':'Coverage', s.procent_obsadzenia+'%', s.liczba_slotow_obsadzonych+'/'+s.liczba_slotow_operacyjnych, 'success') +
        card(pl?'Nieobsadzone':'Unfilled', s.liczba_slotow_nieobsadzonych, '', s.liczba_slotow_nieobsadzonych>0?'alert':'') +
        card(pl?'Alerty type rating':'Type-rating alerts', s.liczba_alertow_tr, '', s.liczba_alertow_tr>0?'alert':'');
    document.getElementById('cards-law').innerHTML =
        card(pl?'Sesje wymagane':'Required sessions', s.liczba_sesji_sym) +
        card(pl?'Godziny / tydzień':'Hours / week', s.godziny_sym_tygodniowo);
}

function tabelaSlotow(sloty){
    let h = `<table><thead><tr><th>${t('base')}</th><th>${t('duty')}</th><th>${t('klasa')}</th><th>${t('min')}</th><th>${t('crew')}</th></tr></thead><tbody>`;
    sloty.forEach(s => {
        let c = [];
        if (s.pic) c.push('PIC: '+osoba(s.pic));
        if (s.fo) c.push((currentLang==='pl'?'2. pilot: ':'FO: ')+osoba(s.fo));
        if (s.instruktor) c.push((currentLang==='pl'?'instruktor: ':'instructor: ')+osoba(s.instruktor));
        const crew = c.length ? c.join('<br>') : `<span style="color:#dc2626;">${t('unfilled')}</span>`;
        h += `<tr><td>${s.baza_id}</td><td>${s.typ_dyzuru}</td><td><span class="badge">${s.wymagana_klasa}</span></td><td><span class="badge badge-${s.wymagana_kategoria_min}">${s.wymagana_kategoria_min}</span></td><td>${crew}</td></tr>`;
    });
    return h + '</tbody></table>';
}

function renderHarmonogram(){
    document.getElementById('harmonogram-content').innerHTML = tabelaSlotow(DANE.sloty || []);
}

let planIdx = 0;
function renderPlan(){
    const P = DANE.plan_15dni || [];
    const cont = document.getElementById('plan-content');
    if (!P.length){ cont.innerHTML=''; return; }
    if (planIdx < 0) planIdx = 0;
    if (planIdx >= P.length) planIdx = P.length-1;
    const d = P[planIdx];
    document.getElementById('plan-data').textContent = d.data + (d.dzien_tygodnia?' ('+d.dzien_tygodnia+')':'');
    document.getElementById('plan-pozycja').textContent = (planIdx+1)+'/'+P.length;
    document.getElementById('plan-podsumowanie').textContent = d.liczba_obsadzonych+'/'+d.liczba_slotow+' '+t('filled');
    document.getElementById('plan-prev').disabled = (planIdx===0);
    document.getElementById('plan-next').disabled = (planIdx===P.length-1);
    cont.innerHTML = planTabela(d.sloty || []);
}
function planPrev(){ planIdx--; renderPlan(); }
function planNext(){ planIdx++; renderPlan(); }

function renderPiloci(){
    const pl = currentLang === 'pl';
    let h = `<table><thead><tr><th>ID</th><th>${t('pilot')}</th><th>${t('kat')}</th><th>${t('base')}</th><th>Org</th><th>${t('ratings')}</th><th>${t('kursy')}</th><th>${t('wolne')}</th><th>${t('ready')}</th></tr></thead><tbody>`;
    (DANE.piloci||[]).forEach(p => {
        const klasy = (p.type_ratings||[]).map(r => r.klasa);
        const med = klasy.includes('MEDEVAC_AW101'); const hems = klasy.includes('HEMS_H145');
        const reqK = med ? 4 : (hems ? 2 : 0);
        let kursyCell;
        if (reqK){
            const ile = (p.kursy||[]).length;
            kursyCell = ile >= reqK ? `<span class="badge badge-B">${ile}/${reqK}</span>` : `<span class="badge badge-D">${ile}/${reqK} ${t('brakKursu')}</span>`;
        } else {
            kursyCell = `<span style="color:#9ca3af;">—</span>`;
        }
        const wolneCell = p.liczba_dni_wolnych ? `<span class="badge badge-C">${p.liczba_dni_wolnych}</span>` : `<span style="color:#9ca3af;">0</span>`;
        const stolBadge = p.stol_prywatnie ? ` <span class="badge ${p.stol_biegly?'badge-B':''}" title="${pl?'prywatny pilot STOL (rejestr wewnętrzny)':'private STOL pilot (internal register)'}">STOL${p.stol_biegly?' \u2713':' \u00b7'}</span>` : '';
        h += `<tr><td><strong>${p.id}</strong></td><td>${p.imie} ${p.nazwisko}</td><td><span class="badge badge-${p.kategoria}">${p.kategoria}</span></td><td>${p.baza_macierzysta}</td><td>${p.organizacja}</td><td>${p.type_ratings.length}${stolBadge}</td><td>${kursyCell}</td><td>${wolneCell}</td><td>${p.gotowy_do_dyzuru?t('tak'):t('nie')}</td></tr>`;
    });
    document.getElementById('piloci-content').innerHTML = h + '</tbody></table>';
}

function renderAlerty(){
    const A = DANE.alerty || [];
    let h = `<table><thead><tr><th>${t('type')}</th><th>${t('pilot')}</th><th>${t('klasa')}</th><th>${t('reason')}</th></tr></thead><tbody>`;
    A.forEach(a => {
        h += `<tr><td>${a.typ}</td><td>${a.imie_nazwisko||a.pilot_id||''}</td><td>${a.klasa||''}</td><td>${a.powod||a.wartosc||''}</td></tr>`;
    });
    if (!A.length) h += `<tr><td colspan="4" style="text-align:center; color:#9ca3af; padding:24px;">—</td></tr>`;
    let out = h + '</tbody></table>';
    const K = DANE.alerty_kursy || [];
    if (K.length){
        out += `<h3>${t('kursAlertNag')}</h3><table><thead><tr><th>${t('pilot')}</th><th>${t('klasa')}</th><th>Slot</th><th>${t('brakKursu')}</th></tr></thead><tbody>`;
        K.forEach(a => {
            out += `<tr><td><strong>${a.pilot_id}</strong> ${a.imie_nazwisko}</td><td>${a.klasa}</td><td>${a.slot_id} (${a.baza_id})</td><td>${a.brakujace.map(x=>`<span class="badge badge-D">${x}</span>`).join(' ')}</td></tr>`;
        });
        out += '</tbody></table>';
    }
    document.getElementById('alerty-content').innerHTML = out;
}

function renderSesje(){
    const S = DANE.sesje_symulatorowe || [];
    const pl = currentLang === 'pl';
    let h = `<table><thead><tr><th>${t('type')}</th><th>${t('pilot')}</th><th>${t('kat')}</th><th>${t('klasa')}</th><th>${t('time')}</th><th>${t('reason')}</th></tr></thead><tbody>`;
    S.forEach(s => {
        const b = s.typ_sesji==='RECURRENT' ? `<span class="badge badge-recurrent">${t('recurrent')}</span>` : `<span class="badge badge-recovery">${t('recovery')}</span>`;
        const powod = pl ? (s.powod||'') : (s.powod_en||s.powod||'');
        h += `<tr><td>${b}</td><td><strong>${s.pilot_id}</strong> ${s.pilot_imie} ${s.pilot_nazwisko}</td><td><span class="badge badge-${s.pilot_kategoria}">${s.pilot_kategoria}</span></td><td>${s.klasa}</td><td>${s.dni_trwania} ${t('dni')} × ${Math.round(s.godziny/s.dni_trwania)} ${t('godzin')}</td><td>${powod}</td></tr>`;
    });
    if (!S.length) h += `<tr><td colspan="6" style="text-align:center; color:#9ca3af; padding:24px;">—</td></tr>`;
    document.getElementById('sesje-content').innerHTML = h + '</tbody></table>';
}

function renderSymulator(){
    const S = DANE.symulator_epde || {oblozenie:[], nieobsadzone:[], liczba_slotow:0, liczba_dni:0, liczba_nieobsadzonych:0};
    const pl = currentLang==='pl';
    const banner = document.getElementById('symulator-banner');
    if (S.liczba_nieobsadzonych > 0){
        banner.className = 'banner warn';
        banner.innerHTML = `<strong>&#9888; ${S.liczba_nieobsadzonych}</strong> ${pl?'sesji nie zmieściło się w oknie — przepełnienie pojemności symulatora.':'sessions did not fit — simulator capacity overflow.'}`;
    } else {
        banner.className = 'banner ok';
        banner.innerHTML = `&#10003; ${pl?'Całe zapotrzebowanie zmieściło się w pojemności.':'All demand fit within capacity.'}`;
    }
    let html = `<p class="muted">${S.liczba_slotow} ${pl?'sesji na':'sessions across'} ${S.liczba_dni} ${pl?'dniach (pojemność 1 pilot / klasę / dzień).':'days (capacity 1 pilot / class / day).'}</p>`;
    html += `<table><thead><tr><th>${t('date')}</th><th>${t('sims')}</th></tr></thead><tbody>`;
    S.oblozenie.forEach(d => {
        const w = d.wpisy.map(x => `<span class="badge">${x.klasa}</span> ${x.pilot} <span class="badge badge-${x.kategoria}">${x.kategoria}</span>`).join('<br>');
        html += `<tr><td><strong>${d.data}</strong></td><td>${w}</td></tr>`;
    });
    document.getElementById('symulator-content').innerHTML = html + '</tbody></table>';
    const nb = document.getElementById('symulator-nieobsadzone');
    if (S.nieobsadzone.length){
        let hh = `<h3>${pl?'Nieobsadzone (przepełnienie)':'Unplaced (overflow)'}</h3><div class="panel"><table><thead><tr><th>${t('pilot')}</th><th>${t('klasa')}</th><th>${t('type')}</th><th>${t('window')}</th></tr></thead><tbody>`;
        S.nieobsadzone.forEach(z => { hh += `<tr><td><strong>${z.pilot_id}</strong></td><td>${z.klasa}</td><td>${z.typ}</td><td>${z.okno_od} – ${z.okno_do}</td></tr>`; });
        nb.innerHTML = hh + '</tbody></table></div>';
    } else { nb.innerHTML = ''; }
}

let lawIdx = 0;
const lawStan = {};   // klucz data|pilot|klasa -> {starty, passed, blad}
function lawKey(d, s){ return d + '|' + s.pilot_id + '|' + s.klasa; }
function lawSetStarty(key, val){ lawStan[key] = lawStan[key] || {}; lawStan[key].starty = parseInt(val,10) || 0; lawStan[key].blad = false; }
function lawSetLadowania(key, val){ lawStan[key] = lawStan[key] || {}; lawStan[key].ladowania = parseInt(val,10) || 0; lawStan[key].blad = false; }
function lawZaliczRecovery(key){
    const st = lawStan[key] || {};
    if ((st.starty || 0) >= 5 && (st.ladowania || 0) >= 5){ st.passed = true; st.blad = false; } else { st.blad = true; }
    lawStan[key] = st; renderLaw();
}
function lawZaliczRecurrent(key){ lawStan[key] = {passed:true}; renderLaw(); }
function renderLaw(){
    const G = DANE.law_grafik_15dni || [];
    const cont = document.getElementById('law-content');
    if (!G.length){ cont.innerHTML=''; return; }
    if (lawIdx < 0) lawIdx = 0;
    if (lawIdx >= G.length) lawIdx = G.length-1;
    const pl = currentLang==='pl';
    const d = G[lawIdx];
    document.getElementById('law-data').textContent = d.data + (d.dzien_tygodnia?' ('+d.dzien_tygodnia+')':'');
    document.getElementById('law-pozycja').textContent = (lawIdx+1)+'/'+G.length;
    document.getElementById('law-liczba').textContent = d.sesje.length + ' ' + t('sesje');
    document.getElementById('law-prev').disabled = (lawIdx===0);
    document.getElementById('law-next').disabled = (lawIdx===G.length-1);
    if (!d.sesje.length){ cont.innerHTML = `<p style="color:#9ca3af; padding:16px;">${t('brakSesji')}</p>`; return; }
    let h = `<table><thead><tr><th>${t('machine')}</th><th>${t('pilot')}</th><th>${t('type')}</th><th>${t('nalot')}</th><th>${t('rejestracja')}</th></tr></thead><tbody>`;
    d.sesje.forEach(s => {
        const key = lawKey(d.data, s);
        const st = lawStan[key] || {};
        const typBadge = s.typ==='RECURRENT' ? `<span class="badge badge-recurrent">${t('recurrent')}</span>` : `<span class="badge badge-recovery">${t('recovery')}</span>`;
        let rej;
        if (st.passed){
            rej = `<span class="badge badge-B">&#10003; ${t('zaliczono')}</span>`;
        } else if (s.typ==='RECURRENT'){
            rej = `<button onclick="lawZaliczRecurrent('${key}')" style="background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:5px 10px;cursor:pointer;">${t('zalicz')}</button>`;
        } else {
            const vs = (st.starty!==undefined) ? st.starty : '';
            const vl = (st.ladowania!==undefined) ? st.ladowania : '';
            const blad = st.blad ? `<div style="color:#c8102e;font-size:11px;margin-top:2px;">min 5 + 5</div>` : '';
            rej = `<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                <label style="font-size:11px;color:#6b7280;">${pl?'starty':'T/O'}<input type="number" min="0" value="${vs}" onchange="lawSetStarty('${key}', this.value)" style="width:54px;padding:4px;margin-left:3px;"></label>
                <label style="font-size:11px;color:#6b7280;">${pl?'lądow.':'LDG'}<input type="number" min="0" value="${vl}" onchange="lawSetLadowania('${key}', this.value)" style="width:54px;padding:4px;margin-left:3px;"></label>
                <button onclick="lawZaliczRecovery('${key}')" style="background:#1a3a5c;color:#fff;border:none;border-radius:4px;padding:5px 10px;cursor:pointer;">${t('zalicz')}</button>
            </div>${blad}`;
        }
        const terminTxt = s.termin ? ` <span style="color:#9ca3af;font-size:11px;">(${t('termin')}: ${s.termin})</span>` : '';
        h += `<tr><td><span class="badge">${s.klasa}</span></td><td>${s.pilot} <span class="badge badge-${s.kategoria}">${s.kategoria}</span></td><td>${typBadge}${terminTxt}</td><td>${s.nalot_na_modelu_h} ${t('godzin')}</td><td>${rej}</td></tr>`;
    });
    cont.innerHTML = h + '</tbody></table>';
}
function lawPrev(){ lawIdx--; renderLaw(); }
function lawNext(){ lawIdx++; renderLaw(); }

function renderAwanse(){
    const A = DANE.awanse || [];
    const pl = currentLang === 'pl';
    const tak = `<span class="badge badge-B">${t('tak')}</span>`, nie = `<span class="badge badge-D">${t('nie')}</span>`;
    let h = `<table><thead><tr>
        <th>${t('pilot')}</th><th>${pl?'Obecna':'Current'}</th><th>${pl?'Cel':'Target'}</th>
        <th>${pl?'Nalot':'Hours'}</th><th>${t('kursy')}</th><th>${pl?'Zatwierdzający':'Approvers'}</th>
        <th>${pl?'Kwalifikuje':'Eligible'}</th></tr></thead><tbody>`;
    A.forEach(a => {
        const nalot = `${a.nalot_calkowity} / ${a.prog_nalotu} ${a.nalot_ok?'✓':'✗'}`;
        const zatw = `${a.zatwierdzajacy}/3 ${a.zatwierdzajacy_ok?'✓':'✗'}`;
        h += `<tr><td><strong>${a.pilot_id}</strong> ${a.imie_nazwisko}</td>
            <td><span class="badge badge-${a.kategoria}">${a.kategoria}</span></td>
            <td><span class="badge badge-${a.cel}">${a.cel}</span></td>
            <td>${nalot}</td><td>${a.kursy_ok?tak:nie}</td><td>${zatw}</td>
            <td>${a.kwalifikuje?tak:nie}</td></tr>`;
    });
    if (!A.length) h += `<tr><td colspan="7" style="text-align:center;color:#9ca3af;padding:24px;">—</td></tr>`;
    document.getElementById('awanse-content').innerHTML = h + '</tbody></table>';
}

function renderMapa(){
    const pl = currentLang === 'pl';
    const S = DANE.siec_reforma || {bazy:[], sektory:[]};
    const bazy = S.bazy || [];
    const SEKT = S.sektory || [];
    const KOLORY = ['#c8102e','#1a3a5c','#0a8754','#b8860b','#6b3fa0','#0e7c86','#d2691e'];
    const kolorSekt = {}; SEKT.forEach((s,i) => kolorSekt[s] = KOLORY[i % KOLORY.length]);

    const W=760, H=820, LON0=14, LON1=24.3, LAT0=49, LAT1=55;
    const X = lon => 30 + (lon-LON0)/(LON1-LON0)*(W-60);
    const Y = lat => 30 + (LAT1-lat)/(LAT1-LAT0)*(H-60);
    const krotka = n => (n||'').split('(')[0].trim();

    // pozycje + indeks CRL po sektorze
    const poz = {}; bazy.forEach(b => poz[b.id] = [X(b.lon), Y(b.lat)]);
    const crl = {}; bazy.forEach(b => { if (b.typ==='CRL') crl[b.sektor] = poz[b.id]; });

    let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:760px;height:auto;background:#f8fafc;border-radius:6px;">`;
    svg += `<rect x="20" y="20" width="${W-40}" height="${H-40}" fill="none" stroke="#e2e6ea"/>`;
    // szprychy sektorów: każda baza (poza CRL) łączy się z CRL swojego sektora
    bazy.forEach(b => {
        if (b.typ==='CRL' || !b.sektor || !crl[b.sektor]) return;
        const [x,y] = poz[b.id], [cx,cy] = crl[b.sektor];
        svg += `<line x1="${x}" y1="${y}" x2="${cx}" y2="${cy}" stroke="${kolorSekt[b.sektor]||'#888'}" stroke-width="4" opacity="0.8" stroke-linecap="round"/>`;
    });
    // węzły
    bazy.forEach(b => {
        const [x,y] = poz[b.id];
        const kol = kolorSekt[b.sektor] || '#9ca3af';
        if (b.typ==='CRL'){
            svg += `<circle cx="${x}" cy="${y}" r="11" fill="#fff" stroke="${kol}" stroke-width="4"/><circle cx="${x}" cy="${y}" r="4.5" fill="${kol}"/>`;
        } else if (b.typ==='CSI-LRM'){
            svg += `<rect x="${x-8}" y="${y-8}" width="16" height="16" rx="2" fill="#fff" stroke="#6b7280" stroke-width="3" transform="rotate(45 ${x} ${y})"/>`;
        } else if (b.typ==='CT-S'){
            svg += `<rect x="${x-7}" y="${y-7}" width="14" height="14" rx="2" fill="#fff" stroke="${kol}" stroke-width="3"/>`;
        } else {
            svg += `<circle cx="${x}" cy="${y}" r="6" fill="#fff" stroke="${kol}" stroke-width="3"/>`;
        }
        const fw = b.typ==='CRL' ? '700' : '600';
        svg += `<text x="${x+12}" y="${y+4}" font-size="11" font-weight="${fw}" fill="#1a3a5c">${krotka(b.nazwa)}</text>`;
    });
    svg += '</svg>';

    let leg = '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:6px;align-items:center;">';
    SEKT.forEach(s => leg += `<span style="font-size:12px;"><span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:${kolorSekt[s]};vertical-align:middle;"></span> ${s}</span>`);
    leg += '</div><div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;color:#6b7280;font-size:12px;">';
    leg += `<span>&#9678; CRL</span><span>&#9711; CT</span><span>&#9633; CT-S ${pl?'(sezon)':'(seasonal)'}</span><span>&#9671; CSI-LRM</span>`;
    const bw = S.liczba_bw_nielokalizowane||0, total = S.liczba_lokalizacji||0;
    leg += `<span>${pl?'Lokalizacji':'Locations'}: ${bazy.length} ${pl?'nazwanych':'named'} / ${total} (${bw} ${pl?'Baz Wsparcia bez lokalizacji w artykułach':'support bases unlocated in articles'})</span>`;
    leg += '</div>';
    document.getElementById('mapa-content').innerHTML = leg + svg;
}

const serwStan = {};
let serwPend = null, serwTimer = null;
function serwClearPend(){ serwPend = null; if (serwTimer){ clearInterval(serwTimer); serwTimer = null; } }
function serwArm(id, akcja){
    serwClearPend();
    serwPend = { id: id, akcja: akcja, sek: 5 };
    serwTimer = setInterval(function(){
        if (!serwPend){ serwClearPend(); return; }
        serwPend.sek -= 1;
        if (serwPend.sek <= 0){ serwClearPend(); }   // okno 5 s minęło — porzuć
        renderSerwis();
    }, 1000);
    renderSerwis();
}
function serwPotwierdz(id, akcja){
    if (serwPend && serwPend.id === id && serwPend.akcja === akcja){
        serwStan[id] = (akcja === 'wezwij');
    }
    serwClearPend(); renderSerwis();
}
function serwPorzuc(){ serwClearPend(); renderSerwis(); }
// kompatybilność wstecz: dawne wywołanie uzbraja wezwanie
function serwWezwij(id){ serwArm(id, 'wezwij'); }

function renderSerwis(){
    const P = DANE.serwis_prognoza || [], W = DANE.serwis_wezwania || [];
    const pl = currentLang === 'pl';
    const PRIO = {WYSOKI: pl?'WYSOKI':'HIGH', SREDNI: pl?'ŚREDNI':'MEDIUM', NISKI: pl?'NISKI':'LOW'};
    const POZ = {POBIEZNY: pl?'pobieżny':'routine', POWAZNY: pl?'poważny':'major', REMONT: pl?'remont':'overhaul'};
    const prioLbl = v => PRIO[v] || v;
    const pozLbl = v => POZ[v] || v;
    const prioBadge = p => { const c = p==='WYSOKI'?'badge-D':(p==='SREDNI'?'badge-C':'badge'); return `<span class="badge ${c}">${prioLbl(p)}</span>`; };
    let h = '';
    if (W.length){
        h += `<div class="banner warn"><strong>${W.length}</strong> ${pl?'egzemplarzy do wezwania priorytetowego na obsługę.':'aircraft for priority service recall.'}</div>`;
    } else {
        h += `<div class="banner ok">${pl?'Brak pilnych wezwań serwisowych.':'No urgent service recalls.'}</div>`;
    }
    h += `<div class="panel"><table><thead><tr><th>${pl?'Maszyna':'Aircraft'}</th><th>${t('klasa')}</th><th>Hub</th><th>${pl?'Nalot':'Hours'}</th><th>${pl?'Do przeglądu':'To service'}</th><th>${pl?'Dni':'Days'}</th><th>${pl?'Priorytet':'Priority'}</th><th>${pl?'Miejsce':'Where'}</th><th>${pl?'Akcja':'Action'}</th></tr></thead><tbody>`;
    P.forEach(p => {
        const serw = p.w_serwisie ? ` <span class="badge">${pl?'w serwisie':'in service'}</span>` : '';
        let akcja;
        const id = p.maszyna_id;
        const BWez = 'background:#c8102e;color:#fff;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:12px;';
        const BPot = 'background:#1a7a3a;color:#fff;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:12px;';
        const BAnu = 'background:#6b7280;color:#fff;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;font-size:12px;';
        const porzuc = `<a onclick="serwPorzuc()" style="cursor:pointer;color:#6b7280;text-decoration:underline;font-size:11px;margin-left:6px;">${pl?'porzuć':'dismiss'}</a>`;
        if (p.w_serwisie){
            akcja = `<span style="color:#9ca3af;">—</span>`;
        } else if (serwPend && serwPend.id === id){
            const etk = serwPend.akcja === 'wezwij' ? (pl?'Potwierdź wezwanie':'Confirm recall') : (pl?'Potwierdź anulowanie':'Confirm cancel');
            akcja = `<button onclick="serwPotwierdz('${id}','${serwPend.akcja}')" style="${BPot}">${etk} (${serwPend.sek})</button>${porzuc}`;
        } else if (serwStan[id]){
            akcja = `<span class="badge badge-B">&#10003; ${pl?'wezwana':'recalled'}</span> <button onclick="serwArm('${id}','anuluj')" style="${BAnu}">${pl?'Anuluj wezwanie':'Cancel recall'}</button>`;
        } else {
            akcja = `<button onclick="serwArm('${id}','wezwij')" style="${BWez}">${pl?'Wezwij na serwis':'Recall'}</button>`;
        }
        h += `<tr><td><strong>${p.maszyna_id}</strong>${serw}</td><td>${p.klasa}</td><td>${p.hub||'—'}</td><td>${p.nalot_h} h</td><td>${pozLbl(p.poziom)} (${p.godziny_do} h)</td><td>${p.dni_do}</td><td>${prioBadge(p.priorytet)}</td><td>${p.miejsce}</td><td>${akcja}</td></tr>`;
    });
    document.getElementById('serwis-content').innerHTML = h + '</tbody></table></div>';
}

function renderCentrum(){
    const C = DANE.centrum_live || {maszyny:[], podsumowanie:{}, bazy:[]};
    const pl = currentLang === 'pl';
    const KOL = {LOT:'#0a8754', ZIEMIA:'#1a3a5c', SERWIS:'#c8102e', NIEOPERACYJNA:'#9ca3af'};
    const ETY = {LOT: pl?'w locie':'in flight', ZIEMIA: pl?'na ziemi':'on ground', SERWIS:'serwis', NIEOPERACYJNA: pl?'nieoperacyjna':'unavailable'};
    let ban = '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:14px;">';
    Object.keys(KOL).forEach(st => { const n = C.podsumowanie[st]||0; ban += `<span style="font-size:13px;"><span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:${KOL[st]};vertical-align:middle;"></span> ${ETY[st]}: <strong>${n}</strong></span>`; });
    ban += '</div>';

    const W=720, H=780, LON0=14, LON1=24.2, LAT0=49, LAT1=55;
    const X = lon => 28 + (lon-LON0)/(LON1-LON0)*(W-56);
    const Y = lat => 28 + (LAT1-lat)/(LAT1-LAT0)*(H-56);
    const jit = (id) => { let s=0; for(let i=0;i<id.length;i++) s=(s*31+id.charCodeAt(i))>>>0; return (s%18)-9; };
    let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:720px;height:auto;background:#f8fafc;border-radius:6px;">`;
    svg += `<rect x="18" y="18" width="${W-36}" height="${H-36}" fill="none" stroke="#e2e6ea"/>`;
    (C.bazy||[]).forEach(b => { const x=X(b.lon), y=Y(b.lat); svg += `<rect x="${x-5}" y="${y-5}" width="10" height="10" fill="#cbd5e1" stroke="#94a3b8"/><text x="${x+9}" y="${y+5}" font-size="12" font-weight="600" fill="#7b8794">${b.id}</text>`; });
    (C.maszyny||[]).forEach(m => { if (m.lat==null||m.lon==null) return; const x=X(m.lon)+jit(m.maszyna_id), y=Y(m.lat)+jit(m.maszyna_id+'y'); svg += `<circle cx="${x}" cy="${y}" r="6.5" fill="${KOL[m.status]||'#888'}" opacity="0.9" stroke="#fff" stroke-width="1"><title>${m.maszyna_id} ${ETY[m.status]}</title></circle>`; });
    svg += '</svg>';

    let tab = `<table><thead><tr><th>${pl?'Maszyna':'Aircraft'}</th><th>${t('klasa')}</th><th>Hub</th><th>Status</th><th>${pl?'Paliwo':'Fuel'}</th><th>${pl?'Czas misji':'Mission'}</th></tr></thead><tbody>`;
    (C.maszyny||[]).forEach(m => {
        const st = `<span class="badge" style="background:${KOL[m.status]}22;color:${KOL[m.status]};">${ETY[m.status]}</span>`;
        tab += `<tr><td><strong>${m.maszyna_id}</strong></td><td>${m.klasa}</td><td>${m.hub||'—'}</td><td>${st}</td><td>${m.paliwo!=null?m.paliwo+'%':'—'}</td><td>${m.czas_misji_min!=null?m.czas_misji_min+' min':'—'}</td></tr>`;
    });
    tab += '</tbody></table>';
    document.getElementById('centrum-content').innerHTML = ban +
        '<div style="display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start;"><div>' + svg +
        '</div><div class="panel" style="flex:1;min-width:320px;">' + tab + '</div></div>';
}

function renderAll(){
    renderDashboard();
    renderHarmonogram();
    renderPlan();
    renderPiloci();
    renderAlerty();
    renderSesje();
    renderSymulator();
    renderLaw();
    renderAwanse();
    renderMapa();
    renderSerwis();
    renderCentrum();
}
renderAll();
</script>
<footer style="text-align:center;color:#9ca3af;font-size:11px;padding:18px 0;border-top:1px solid #eef0f3;margin-top:24px;">&#169; 2026 Maciej M. Kasperek ("vonKrappitz") &middot; Apache-2.0 &middot; FRMS proof-of-concept</footer>
</body>
</html>
"""


def zbuduj_web(sciezka: str = "frms-web.html") -> str:
    dane = eksport_do_json()
    blob = json.dumps(dane, ensure_ascii=False)
    html = SZABLON.replace(ZNACZNIK, blob, 1)
    Path(sciezka).write_text(html, encoding="utf-8")
    return sciezka


if __name__ == "__main__":
    p = zbuduj_web()
    print("Zapisano", p)
