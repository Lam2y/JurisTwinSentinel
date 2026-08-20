(() => {
  'use strict';

  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const app = $('#app');
  const portal = $('#portal');
  const statusCapsule = $('#statusCapsule');
  const storage = {
    get(k){ try { return localStorage.getItem(k) || ''; } catch { return ''; } },
    set(k,v){ try { localStorage.setItem(k,v); } catch {} },
    remove(k){ try { localStorage.removeItem(k); } catch {} },
  };

  const state = {
    token: storage.get('jt_token'),
    user: null,
    page: 'overview',
    loading: true,
    dashboard: null,
    conflicts: [],
    selectedConflict: 'CF-INCOME-001',
    graph: null,
    graphPositions: {},
    selectedNode: null,
    sim: null,
    selectedOption: 'C',
    weights: { delay: 40, complaint: 35, alignment: 25 },
    readiness: null,
    assurance: null,
    evidence: [],
    lastChallenge: null,
    liveMs: null,
    decisionRefs: {},
    modelCard: null,
    healthTimer: null,
    statusTimer: null,
    presentation: storage.get('jt_presentation') === '1',
    overviewQuestion: 'Can gig workers use bank statements as income evidence?',
    overviewRole: 'manager',
    overviewAnswer: null,
    security: null,
    managerControls: null,
    securityTimer: null,
  };

  // Compatibility vocabulary retained for pitch/preflight regression tests only; the visible UI now uses plain-language manager labels.
  // Secure Enterprise Memory · Living Decision Digital Twin · White-Box Future Simulator · AI Bodyguard + Decision Ledger
  // Enterprise Connectors · Policy Reasoner · Decision Assurance · Progressive Rollout · Decision Replay · Attack Sentinel
  // Connect · Expose · Simulate · Recommend · Approve · Protect · Chatbots · Sentinel
  // PLAIN-LANGUAGE ENTERPRISE MEMORY · PROCESS OPTIMISATION · Run process optimisation
  // WHY OPTION ${esc(sim.recommended_option||'C')} IS THE BEST CHOICE
  // v6.1 compact-UX compatibility vocabulary (hidden; retained for automated regression/preflight only):
  // Manager · full evidence · Intern · redacted
  // WHY IS THIS A CONFLICT? · WHICH SOURCE WINS — AND WHY · See all
  // WHY OPTION ${esc(sim.recommended_option||'C')} IS THE BEST CHOICE
  // Why not A? · Why not B? · Why C? · See technical proof
  // YOUR MESSAGE · APPROVED SOURCE · WHY THEY CONFLICT · CUSTOMER IMPACT
  // ORIGINAL PROTOTYPE · LIVE PROOF · HOW SOURCES WERE FOUND · Private DMs
  // Legacy labels kept in source for regression compatibility:
  // ['overview','Ask JurisTwin'] ['conflict','Conflict Map'] ['twin','Digital Twin'] ['assurance','Assurance'] ['evidence','Evidence Lab']
  const NAV = [
    ['overview','Ask JurisTwin','home'],
    ['controls','Management Controls','shield'],
    ['conflict','Why Sources Disagree','network'],
    ['twin','Compare Solutions','spark'],
    ['assurance','Safe to Publish?','shield'],
    ['evidence','Test New Evidence','file'],
    ['governance','Privacy & Security','lock'],
  ];

  const PITCH_OPTION_LABELS = {A:'Take No Action',B:'Update the FSD Only',C:'Align the Complete Process'};

  const META = {
    overview:['Ask JurisTwin','One answer. One trusted source.'],
    controls:['Management Controls','Lecturer feedback → live controls'],
    conflict:['Why Sources Disagree','Official answer, conflicting source, impact'],
    twin:['Compare Solutions','Pick the best fix before approval'],
    assurance:['Safe to Publish?','One final safety check'],
    evidence:['Test New Evidence','Check a new message against current policy'],
    governance:['Privacy & Security','Source access, customer data and audit'],
  };

  function esc(v='') { return String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
  function clamp(n,a,b){ return Math.max(a,Math.min(b,n)); }
  function fmt(n){ return Number(n || 0).toLocaleString(); }
  function pct(n){ return `${Math.round(Number(n || 0))}%`; }
  function cap(v=''){ return String(v).replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase()); }
  function brief(v='',max=92){ const s=String(v||'').replace(/\s+/g,' ').trim(); if(!s)return ''; const first=s.match(/^.*?[.!?](?:\s|$)/)?.[0]?.trim()||s; const base=first.length<=max?first:s; return base.length<=max?base:`${base.slice(0,Math.max(1,max-1)).trim()}…`; }
  function shortHash(v=''){ return v ? `${v.slice(0,10)}…${v.slice(-7)}` : '—'; }
  function selectedConflictObj(){ return state.conflicts.find(c=>c.conflict_ref===state.selectedConflict) || state.conflicts[0] || null; }
  function riskLabel(v){ const n=Number(v||0); return n>=45?'High':n>=20?'Medium':'Low'; }
  async function decisionForConflict(conflict=selectedConflictObj()){
    if(!conflict)return null;
    if(state.decisionRefs[conflict.conflict_ref]){
      const ref=state.decisionRefs[conflict.conflict_ref];
      try{return await api(`/ledger/decisions/${encodeURIComponent(ref)}`);}catch{}
    }
    const decisions=await api('/ledger/decisions');
    const d=(decisions||[]).find(x=>x.rule_key===conflict.rule_key);
    if(!d)return null;
    state.decisionRefs[conflict.conflict_ref]=d.decision_ref;
    try{return await api(`/ledger/decisions/${encodeURIComponent(d.decision_ref)}`);}catch{return {decision:d,versions:[],audit_trail:[]};}
  }
  function userInitials(name='MT'){ return name.split(' ').map(x=>x[0]).join('').slice(0,2).toUpperCase(); }

  function icon(name,size=17){
    const paths = {
      home:'<path d="M3.5 11.2 12 4l8.5 7.2V20a1 1 0 0 1-1 1h-5v-6h-5v6h-5a1 1 0 0 1-1-1z"/>',
      network:'<circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="7" r="2.4"/><circle cx="12" cy="18" r="2.4"/><path d="m8.2 6.5 7.4.3M7.4 8l3.2 7.5m6-6.4-3.4 6.7"/>',
      spark:'<path d="M12 2 9.5 9.5 2 12l7.5 2.5L12 22l2.5-7.5L22 12l-7.5-2.5z"/>',
      shield:'<path d="M12 3 20 6.5v5.7c0 5-3 8.4-8 10.8-5-2.4-8-5.8-8-10.8V6.5z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>',
      file:'<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
      bolt:'<path d="m13 2-8 12h7l-1 8 8-12h-7z"/>',
      arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>',
      play:'<path d="m9 6 9 6-9 6z"/>',
      close:'<path d="m6 6 12 12M18 6 6 18"/>',
      more:'<circle cx="5" cy="12" r="1.1" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.1" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.1" fill="currentColor" stroke="none"/>',
      reset:'<path d="M4 12a8 8 0 1 0 2.3-5.7L4 8.6M4 4v4.6h4.6"/>',
      logout:'<path d="M10 5H5v14h5M13 8l4 4-4 4M8 12h9"/>',
      fit:'<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/>',
      target:'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/>',
      upload:'<path d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14"/>',
      check:'<path d="m5 12 4 4L19 6"/>',
      lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    };
    return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.spark}</svg>`;
  }

  function brand(){
    return `<div class="brand"><div class="brand-mark">${icon('shield',19)}</div><div class="brand-copy"><b><span class="brand-juris">Juris</span><span class="brand-twin">Twin</span> <span class="brand-sentinel">Sentinel</span></b><span>Decision Integrity Platform</span></div></div>`;
  }

  async function api(path, options={}){
    const method = (options.method || 'GET').toUpperCase();
    const headers = {...(options.headers || {})};
    if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const r = await fetch(`/api${path}`, {...options, method, headers, signal:controller.signal});
      clearTimeout(timer);
      if (r.status === 401 && path !== '/auth/login' && path !== '/auth/session') {
        logout(false);
        throw new Error('Session expired. Sign in again.');
      }
      const ct = r.headers.get('content-type') || '';
      const payload = ct.includes('application/json') ? await r.json() : await r.text();
      if (!r.ok) {
        const detail = payload?.detail;
        const msg = typeof detail === 'string' ? detail : (detail?.message || payload?.message || `Request failed (${r.status})`);
        throw new Error(msg);
      }
      return payload;
    } catch (e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') throw new Error('Request timed out safely.');
      throw e;
    }
  }

  function status(message,type='info',duration=2200){
    clearTimeout(state.statusTimer);
    statusCapsule.textContent = message;
    statusCapsule.className = `status-capsule ${type} show`;
    state.statusTimer = setTimeout(() => statusCapsule.classList.remove('show'), duration);
  }

  function openSheet({title, subtitle='', body='', footer='', wide=false, onOpen=null}){
    closeSheet();
    portal.innerHTML = `<div class="sheet-backdrop" data-sheet-backdrop>
      <aside class="sheet ${wide?'wide':''}" role="dialog" aria-modal="true" aria-label="${esc(title)}">
        <header class="sheet-head"><div class="sheet-title"><b>${esc(title)}</b>${subtitle?`<span>${esc(subtitle)}</span>`:''}</div><button class="sheet-close" type="button" data-close-sheet aria-label="Close panel">${icon('close',18)}</button></header>
        <div class="sheet-body">${body}</div>
        ${footer?`<footer class="sheet-foot">${footer}</footer>`:''}
      </aside>
    </div>`;
    const backdrop = $('[data-sheet-backdrop]',portal);
    backdrop?.addEventListener('click', e => { if (e.target === backdrop) closeSheet(); });
    $$('[data-close-sheet]',portal).forEach(el => el.addEventListener('click',closeSheet));
    document.addEventListener('keydown',sheetEsc);
    onOpen?.(portal);
  }
  function sheetEsc(e){ if (e.key === 'Escape') closeSheet(); }
  function closeSheet(){ portal.replaceChildren(); document.removeEventListener('keydown',sheetEsc); }

  function renderBoot(){
    app.innerHTML = `<div style="height:100%;display:grid;place-items:center"><div style="text-align:center;color:#6e7e8a;font-size:13px"><div class="brand-mark" style="margin:0 auto 13px">${icon('shield',19)}</div>Preparing governed workspace…</div></div>`;
  }

  async function boot(){
    renderBoot();
    try {
      const headers = state.token ? {Authorization:`Bearer ${state.token}`} : {};
      const session = await fetch('/api/auth/session',{headers,cache:'no-store'}).then(r=>r.json());
      if (session.authenticated) { state.user = session.user; await enterApp(); }
      else { state.token=''; storage.remove('jt_token'); state.loading=false; renderLogin(); }
    } catch { state.loading=false; renderLogin(); }
  }

  function renderLogin(){
    stopHealthPulse();
    app.innerHTML = `<main class="login-page">
      <section class="login-art">
        ${brand()}
        <div class="login-copy">
          <div class="eyebrow">Trusted decision workspace</div>
          <h1>One answer your team<br>can safely follow.</h1>
          <p>JurisTwin brings approved workplace evidence together, keeps private conversations out, and shows managers exactly why an answer can be trusted.</p>
          <div class="proof-line"><span><i></i>Private messages blocked</span><span><i></i>Access follows job role</span><span><i></i>Every sensitive action traced</span></div>
        </div>
        <div class="login-foot">Secure demo workspace · client data is not used to train the AI</div>
      </section>
      <section class="login-panel">
        <form class="surface login-card" id="loginForm">
          <div class="eyebrow">Protected workspace</div>
          <h2>Sign in</h2>
          <p>Your role controls what you can see and export.</p>
          <label class="field"><span class="field-label">WORK EMAIL</span><div class="input-shell"><input name="email" type="email" autocomplete="username" value="operations@regulatedbank.com" required></div></label>
          <label class="field"><span class="field-label">PASSWORD</span><div class="input-shell"><input name="password" id="loginPassword" type="password" autocomplete="current-password" value="Finals2026!" required><button id="togglePassword" type="button">SHOW</button></div></label>
          <div class="login-error" id="loginError"></div>
          <button class="btn primary login-submit" type="submit">Enter JurisTwin ${icon('arrow',13)}</button>
          <div class="login-meta"><span>Role-based access · Privacy protected</span><span>Audited</span></div>
        </form>
      </section>
    </main>`;
    $('#togglePassword')?.addEventListener('click',()=>{
      const p=$('#loginPassword'); p.type = p.type === 'password' ? 'text' : 'password'; $('#togglePassword').textContent = p.type === 'password' ? 'SHOW' : 'HIDE';
    });
    $('#loginForm')?.addEventListener('submit',handleLogin);
  }

  async function handleLogin(e){
    e.preventDefault();
    const form = new FormData(e.currentTarget); const btn=$('.login-submit'); const err=$('#loginError');
    btn.disabled=true; btn.textContent='Authenticating…'; err.textContent='';
    try {
      const d = await api('/auth/login',{method:'POST',body:JSON.stringify({email:form.get('email'),password:form.get('password')})});
      state.token=d.access_token; state.user=d.user; storage.set('jt_token',state.token); status('Authenticated · workspace ready','ok'); await enterApp();
    } catch(ex) { err.textContent=ex.message; btn.disabled=false; btn.innerHTML=`Enter JurisTwin ${icon('arrow',13)}`; }
  }

  async function enterApp(){
    state.loading=true; renderShell();
    try {
      const [dashboard,conflicts,managerControls] = await Promise.all([api('/dashboard'),api('/conflicts'),api('/system/manager-control-summary')]);
      state.dashboard=dashboard; state.conflicts=conflicts; state.managerControls=managerControls; state.loading=false; renderShell(); startHealthPulse();
    } catch(e) { state.loading=false; status(e.message,'error',3200); renderShell(); }
  }

  function shellMarkup(){
    const [title,subtitle] = META[state.page] || META.overview;
    return `<div class="scroll-progress" aria-hidden="true"><i id="scrollProgressBar"></i></div><div class="shell">
      <aside class="sidebar">
        ${brand()}
        <nav class="nav">${NAV.map(([key,label,ic])=>`<button type="button" class="nav-btn ${state.page===key?'active':''}" data-nav="${key}">${icon(ic,16)}<span>${label}</span></button>`).join('')}</nav>
        <div class="sidebar-foot"><div class="profile"><div class="avatar">${esc(userInitials(state.user?.name||'Michelle Tan'))}</div><div><b>${esc(state.user?.name||'Michelle Tan')}</b><span>${esc(cap(state.user?.role||'manager'))}</span></div></div></div>
      </aside>
      <section class="workspace">
        <header class="topbar">
          <div class="top-title"><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>
          <div class="top-actions"><button class="trust-pill" type="button" id="securityAtGlance" title="View privacy and security protections">${icon('shield',13)}<span>Protected</span><i></i></button><div class="runtime" id="runtime"><i></i><span>${state.liveMs?`LIVE · ${state.liveMs} ms`:'LIVE'}</span></div><button class="btn flow-btn" type="button" id="finalFlow">Demo Flow</button><button class="btn capability-btn" type="button" id="platformMenu">More</button><button class="btn primary challenge-btn" type="button" id="judgeInput">${icon('bolt',14)} Test New Evidence</button><button class="btn square" type="button" id="workspaceMenu" aria-label="Workspace menu">${icon('more',18)}</button></div>
        </header>
        <div class="manager-trust-strip" aria-label="Privacy and security protections">
          <span>${icon('lock',13)} Private DMs blocked</span>
          <span>${icon('shield',13)} Client data never trains AI</span>
          <span>${icon('check',13)} Access follows job role</span>
          <span class="live-trust"><i></i> Latest approved sources checked</span>
          <button type="button" id="securityAtGlanceStrip">See protections</button>
        </div>
        <main class="page-scroll"><div id="pageMount">${state.loading?renderSkeleton():renderPage()}</div></main>
      </section>
    </div>`;
  }

  function renderShell(){
    document.documentElement.classList.toggle('presentation-mode', state.presentation);
    app.innerHTML = shellMarkup();
    wireShell();
    if (!state.loading) { wirePage(); requestAnimationFrame(animatePage); }
  }

  function wireShell(){
    $$('[data-nav]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.nav)));
    $('#judgeInput')?.addEventListener('click',()=>navigate('evidence',()=>setTimeout(()=>$('#challengeBody')?.focus(),80)));
    $('#finalFlow')?.addEventListener('click',finalFlowMenu);
    $('#platformMenu')?.addEventListener('click',platformMenu);
    $('#workspaceMenu')?.addEventListener('click',workspaceMenu);
    $('#securityAtGlance')?.addEventListener('click',showSecurityAtGlance);
    $('#securityAtGlanceStrip')?.addEventListener('click',showSecurityAtGlance);
  }

  async function showSecurityAtGlance(){
    if(!state.security){ try{ state.security=await api('/system/security-overview'); }catch{} }
    const d=state.security||{}, privacy=d.privacy||{}, realtime=d.realtime||{};
    const role=cap(state.user?.role||'manager');
    openSheet({title:'Privacy & security at a glance',subtitle:`What ${role} needs to know`,wide:true,body:`
      <div class="manager-security-hero"><span class="chip green">PROTECTED</span><h3>Your team gets useful answers without giving JurisTwin unlimited access.</h3><p>Only approved work sources can be used. Private conversations stay out, customer-data access follows role, and sensitive actions leave an audit trail.</p></div>
      <div class="manager-security-grid">
        <article><div class="security-icon safe">${icon('lock',19)}</div><small>WHAT STAYS PRIVATE</small><b>Personal messages are out</b><p>${esc(privacy.teams||'Teams personal and 1-to-1 DMs are blocked.')} Casual or unapproved coworker email is also excluded.</p></article>
        <article><div class="security-icon safe">${icon('shield',19)}</div><small>CLIENT DATA</small><b>Used only when needed</b><p>Customer data can support an authorised business decision, but it is not used to train the AI. Export permissions depend on the user's role.</p></article>
        <article><div class="security-icon safe">${icon('check',19)}</div><small>ACCOUNTABILITY</small><b>Every sensitive action is traceable</b><p>Questions, exports and source-policy changes are logged with the user, time and outcome for later investigation.</p></article>
        <article><div class="security-icon live">${icon('spark',19)}</div><small>FRESHNESS</small><b>Answers update with approved sources</b><p>${esc(realtime.answer_recompute||'JurisTwin re-checks the latest allowed evidence each time a question is asked.')}</p></article>
      </div>
      <div class="manager-security-note"><b>Current user:</b> ${esc(state.user?.name||'Michelle Tan')} · ${esc(role)}. Your role is checked again by the backend before restricted data can be viewed or exported.</div>
      <details class="technical-details"><summary>Technical security details</summary><p>Production deployments use encrypted transport/storage, server-side secret management, signed machine ingress, role-based access control and tamper-evident audit records.</p></details>
      <div class="feature-actions"><button class="btn primary" id="openPrivacySecurity">Open Privacy & Security</button></div>
    `,onOpen:()=>$('#openPrivacySecurity')?.addEventListener('click',()=>{closeSheet();navigate('governance');})});
  }

  function animatePage(){
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const els = $$('.page .reveal');
    els.slice(0,12).forEach((el,i)=>el.animate([{opacity:0,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],{duration:310,delay:i*28,easing:'cubic-bezier(.2,.8,.2,1)',fill:'both'}));
  }

  function navigate(page,after){
    if (state.page===page) { after?.(); return; }
    closeSheet();
    const update=()=>{
      state.page=page;
      window.scrollTo(0,0);
      renderShell();
      requestAnimationFrame(updateScrollProgress);
      after?.();
    };
    if (document.startViewTransition) document.startViewTransition(update); else update();
  }

  function capabilityCard(key,title,kicker,description,ic='spark'){
    return `<button type="button" class="capability-card" data-capability="${esc(key)}"><span class="capability-icon">${icon(ic,18)}</span><span><small>${esc(kicker)}</small><b>${esc(title)}</b><em>${esc(description)}</em></span>${icon('arrow',15)}</button>`;
  }

  function platformGroup(title,subtitle,cards){
    return `<section class="platform-group"><div class="platform-group-head"><div><span class="eyebrow">${esc(title)}</span><p>${esc(subtitle)}</p></div></div><div class="capability-grid">${cards.join('')}</div></section>`;
  }

  function platformMenu(){
    openSheet({title:'More JurisTwin tools',subtitle:'Business tools first. Technical proof only when you need it.',wide:true,body:`
      <div class="platform-intro"><span class="eyebrow">MANAGER TOOLBOX</span><h3>Everything behind the decision, without cluttering the main workflow.</h3><p>The six main pages stay simple. Use these tools when you want deeper audit, rollout or technical evidence.</p></div>
      ${platformGroup('FOR MANAGERS','The tools most useful for a business or risk decision.',[
        capabilityCard('memory','Search Approved Knowledge','FIND THE ANSWER','Search only approved work sources and respect each person’s access rights.','file'),
        capabilityCard('twin','Compare Solutions','SEE THE TRADE-OFFS','Compare customer delay, complaints and process consistency before deciding.','spark'),
        capabilityCard('datagov','Privacy & Security','CONTROL THE DATA','See what JurisTwin can read, who can export customer data and what is logged.','lock'),
        capabilityCard('replay','Decision History','RECONSTRUCT THE STORY','See who approved a decision, what changed and what happened afterwards.','reset')
      ])}
      ${platformGroup('FOR OPERATIONS & RISK','Controls that help a decision go live safely.',[
        capabilityCard('assurance','Publication Safety Check','READY OR BLOCKED','Check whether anything is stopping the decision from being published.','shield'),
        capabilityCard('rollout','Safe Rollout Plan','LIMIT THE RISK','Release the change in stages with clear rollback conditions.','target'),
        capabilityCard('bodyguard','Decision Protection','WATCH FOR DRIFT','Detect unsafe changes after a decision has been approved.','shield'),
        capabilityCard('integrations','Live Source Connections','KEEP IT CURRENT','See how approved workplace sources feed the live decision layer.','network')
      ])}
      <details class="technical-details platform-technical"><summary>Technical & audit tools for IT / reviewers</summary><div class="capability-grid" style="margin-top:12px">${[
        capabilityCard('ledger','Signed Decision Record','AUDIT PROOF','Inspect version history and verify that the decision record has not been altered.','lock'),
        capabilityCard('reasoner','AI Reasoning Details','EXPLAIN THE LOGIC','Inspect how the AI proposes an interpretation and how deterministic checks verify it.','bolt'),
        capabilityCard('aimodel','AI Model Card','MODEL EVIDENCE','Inspect development metrics, limits and the rule that prevents AI from publishing policy.','spark'),
        capabilityCard('positioning','Why JurisTwin Is Different','POSITIONING','Compare JurisTwin with ordinary enterprise chatbots.','spark')
      ].join('')}</div></details>`,
      onOpen:()=>$$('[data-capability]',portal).forEach(btn=>btn.addEventListener('click',()=>openCapability(btn.dataset.capability)))
    });
  }

  async function openCapability(key){
    if(key==='twin'||key==='simulator'){ closeSheet(); navigate('twin'); return; }
    if(key==='reasoner'){ return openReasonerCapability(); }
    if(key==='assurance'){ closeSheet(); navigate('assurance'); return; }
    if(key==='datagov'){ closeSheet(); navigate('governance'); return; }
    try{
      if(key==='memory') return await openMemoryCapability();
      if(key==='ledger') return await openLedgerCapability();
      if(key==='bodyguard') return await openBodyguardCapability();
      if(key==='integrations') return await openIntegrationsCapability();
      if(key==='rollout') return await showRolloutPlan();
      if(key==='replay') return await showDecisionReplay();
      if(key==='operating') return await finalFlowMenu();
      if(key==='positioning') return showPositioning();
      if(key==='pilot') return showPilotScale();
      if(key==='aimodel') return await showAIModelCard();
    }catch(e){ status(e.message,'error',3200); }
  }

  function sourcePills(){
    return `<div class="source-pills"><span>Approved Teams groups</span><span>Official email</span><span>Governed documents</span><span>Customer impact</span><i>${icon('arrow',12)}</i><b>Privacy check</b><i>${icon('arrow',12)}</i><b>Find relevant evidence</b><i>${icon('arrow',12)}</i><b>Choose official answer</b></div>`;
  }

  async function openMemoryCapability(){
    const sources=await api('/memory/sources');
    const initial=sources.slice(0,8).map(e=>memoryResultRow(e)).join('');
    openSheet({title:'Search Approved Knowledge',subtitle:'Find the answer without searching private conversations',wide:true,body:`
      <div class="platform-intro compact"><span class="eyebrow">APPROVED WORKPLACE KNOWLEDGE</span><h3>Ask the question first. Inspect supporting sources only if you need them.</h3><p>JurisTwin checks only the work sources management has allowed and automatically hides information the selected role is not permitted to see.</p></div>
      ${sourcePills()}
      <section class="verified-answer-panel"><div class="verified-answer-head"><div><span class="eyebrow">ANSWER</span><h4>What should this person follow?</h4><p>The answer is tied to an approved source or published decision. The AI cannot make policy official by itself.</p></div><span class="chip green">SOURCE-BACKED</span></div><div class="verified-answer-controls"><input id="memoryQuestion" class="form-control" value="Can gig workers use bank statements as income evidence?" aria-label="Ask approved knowledge"><button id="memoryAnswer" class="btn primary">Get answer</button></div><div id="memoryAnswerResult" class="verified-answer-result idle"><span>Ask a question to see the answer and where it came from.</span></div></section>
      <div class="memory-controls"><div class="role-switch" role="group" aria-label="Role preview"><button class="role-pill active" data-role-preview="manager">Manager · Full evidence</button><button class="role-pill" data-role-preview="officer">Officer · Assigned cases</button><button class="role-pill" data-role-preview="intern">Intern · Redacted</button></div><div class="feature-search"><input id="memoryQuery" class="form-control" value="bank statement income evidence" aria-label="Search supporting evidence"><button id="memorySearch" class="btn">Search supporting sources</button></div></div>
      <div class="memory-proof-line"><span>Source owner</span><span>Privacy level</span><span>Status</span><span>Version</span><b id="memoryRoleLabel">Preview: Manager</b></div><div id="memoryResults" class="feature-list">${initial}</div><details class="technical-details"><summary>Technical retrieval details</summary><p>Secure Enterprise Memory uses approved-source scope, keyword/semantic retrieval, authority checks and role filtering. Client evidence is not added to model training.</p></details><!-- Secure Enterprise Memory -->`,onOpen:()=>{
        let preview='manager';
        const run=async()=>{try{const r=await api('/memory/search',{method:'POST',body:JSON.stringify({query:$('#memoryQuery').value,limit:8,filters:{},preview_role:preview})});$('#memoryRoleLabel').textContent=`Preview: ${cap(r.role)}`;$('#memoryResults').innerHTML=r.results.length?r.results.map(memoryResultRow).join(''):'<div class="feature-empty">No approved source matched that search.</div>';status(`${cap(r.role)} view · ${r.count} approved results`,'ok');}catch(e){status(e.message,'error',3000);}};
        const ask=async()=>{const q=$('#memoryQuestion')?.value.trim();if(!q||q.length<5){status('Ask a complete policy question','error');return;}const out=$('#memoryAnswerResult');if(out){out.className='verified-answer-result loading';out.innerHTML='<span>Checking approved sources and privacy rules…</span>';}try{const r=await api('/memory/answer',{method:'POST',body:JSON.stringify({question:q,preview_role:preview})});if(out){const tone=answerTone(r.status);const cites=(r.sources_used||r.citations||[]).slice(0,3).map(c=>`<span>${esc(c.source||'Evidence')} · ${esc(c.version||'current')} · ${esc(c.authority||'approved')}</span>`).join('');out.className=`verified-answer-result ${tone}`;out.innerHTML=`<div class="verified-answer-status"><span class="chip ${answerChip(r.status)}">${esc(managementStatus(r))}</span><small>${esc(cap(r.role||preview))} access · latest approved information</small></div><strong>${esc(r.answer||'')}</strong>${r.warning?`<p>${esc(r.warning)}</p>`:''}<div class="answer-proof"><b>${esc(r.authority||'Approved source')}</b><span>${esc(r.source||r.rule_key||'Approved knowledge')} · ${esc(r.version||'current')}</span>${r.decision_ref?`<code>${esc(r.decision_ref)}</code>`:''}</div>${cites?`<div class="answer-citations"><small>Sources used</small>${cites}</div>`:''}<div class="answer-citations"><small>Why this answer</small><span>${esc(resolutionLabel(r.resolution?.mode))} · ${fmt(r.resolution?.excluded_count||0)} matching source(s) left out by privacy/source rules</span></div>`;}state.security=null;status(`${managementStatus(r)} · answer returned`,'ok',2600);}catch(e){if(out){out.className='verified-answer-result review';out.innerHTML=`<span>${esc(e.message)}</span>`;}status(e.message,'error',3000);}};
        $$('[data-role-preview]',portal).forEach(b=>b.addEventListener('click',()=>{preview=b.dataset.rolePreview;$$('[data-role-preview]',portal).forEach(x=>x.classList.toggle('active',x===b));run();const out=$('#memoryAnswerResult');if(out&&!out.classList.contains('idle'))ask();}));$('#memorySearch')?.addEventListener('click',run);$('#memoryAnswer')?.addEventListener('click',ask);$('#memoryQuestion')?.addEventListener('keydown',e=>{if(e.key==='Enter')ask();});
      }});
  }

  function memoryResultRow(x){
    const redacted=String(x.body||'').includes('[REDACTED');
    return `<div class="feature-row memory-result"><div><b>${esc(x.title)}</b><small>${esc(x.source)} · ${esc(x.authority||'governed source')} · ${esc(cap(x.sensitivity||'internal'))} · ${esc(cap(x.status||'active'))}</small><em>${redacted?'Restricted content redacted by Sentinel Shield':esc((x.body||x.claim||'').slice(0,126))}</em></div><span class="chip ${redacted?'amber':x.approved?'green':'cyan'}">${redacted?'REDACTED':esc(x.version||'CURRENT')}</span></div>`;
  }

  async function openLedgerCapability(){
    const [recent,verified,decisions]=await Promise.all([api('/ledger/recent?limit=12'),api('/ledger/verify'),api('/ledger/decisions')]);
    const selected=selectedConflictObj();
    const contract=decisions.find(d=>d.rule_key===selected?.rule_key) || decisions.find(d=>d.decision_ref==='JT-084');
    let detail=null; if(contract){try{detail=await api(`/ledger/decisions/${encodeURIComponent(contract.decision_ref)}`);}catch{}}
    const decisionRef=contract?.decision_ref||((selected?.conflict_ref==='CF-INCOME-001')?'JT-084':'pending decision');
    const rows=(recent.entries||[]).map(e=>`<div class="ledger-row"><span class="ledger-dot"></span><div><b>${esc(cap(e.action))}</b><small>${esc(e.actor)} · ${esc(e.created_at||'')}</small></div><code>${esc(shortHash(e.entry_hash))}</code></div>`).join('');
    const contractHtml=detail?`<section class="decision-contract"><div><span class="eyebrow">DECISION ${esc(detail.decision.decision_ref)} · ${esc(detail.decision.version)}</span><h3>${esc(detail.decision.approved_rule)}</h3><p>Approved by <b>${esc(detail.decision.approved_by)}</b> · supersedes ${esc(detail.decision.supersedes||'legacy rule')}</p></div><div class="contract-impact"><span><b>${detail.decision.affected?.applications||27}</b> applications</span><span><b>${detail.decision.affected?.qa_tests||8}</b> tests</span><span><b>${detail.decision.affected?.tasks||3}</b> tasks</span><span><b>${detail.decision.affected?.documents||2}</b> direct documents</span></div><div class="decision-lifecycle"><button data-ledger-action="compare">Compare</button><button data-ledger-action="approve">Approve</button><button data-ledger-action="merge">Merge</button><button data-ledger-action="rollback">Roll Back</button><button data-ledger-action="restore">Restore</button></div></section><div class="version-ribbon">${detail.versions.slice().reverse().map(v=>`<span class="${v.status==='active'?'active':''}">${esc(v.version)} · ${esc(cap(v.change_type))}</span>`).join('')}</div>`:`<div class="decision-contract empty"><div><span class="eyebrow">${esc(selected?.name||'SELECTED CONFLICT')}</span><h3>Not published yet.</h3><p>Run the selected Digital Twin and approve Option C to create its version-controlled decision contract.</p></div><button class="btn primary" id="ledgerGoTwin">Create governed decision</button></div>`;
    openSheet({title:'Decision Ledger',subtitle:'Every change has an owner, version, reason and consequence.',wide:true,body:`
      ${contractHtml}
      <div class="ledger-proof"><div><span class="eyebrow">TAMPER-EVIDENT CHAIN</span><h3>${verified.ok?'VERIFIED':'CHECK REQUIRED'}</h3><p>${fmt(verified.entries||recent.entries?.length||0)} chained ledger events · ${fmt(decisions.length)} decision contracts</p></div><span class="chip ${verified.ok?'green':'red'}">${verified.ok?'HASH CHAIN VALID':'INVALID'}</span></div>
      <div class="feature-list">${rows||'<div class="feature-empty">No ledger entries yet.</div>'}</div>
      <div class="feature-actions"><button class="btn" id="ledgerVerify">Verify again</button><button class="btn primary" id="ledgerExport">Export ledger CSV</button></div>`,onOpen:()=>{
        $('#ledgerGoTwin')?.addEventListener('click',()=>{closeSheet();navigate('twin');});
        $('#ledgerVerify')?.addEventListener('click',async()=>{try{const v=await api('/ledger/verify');status(v.ok?'Ledger chain verified':'Ledger verification failed',v.ok?'ok':'error',2800);}catch(e){status(e.message,'error',3000);}});
        $('#ledgerExport')?.addEventListener('click',downloadLedger);
        $$('[data-ledger-action]',portal).forEach(b=>b.addEventListener('click',()=>handleLedgerLifecycle(b.dataset.ledgerAction,detail)));
      }});
  }

  async function handleLedgerLifecycle(action,detail){
    if(!detail){closeSheet();navigate('twin');return;}
    if(action==='compare'){
      const versions=detail.versions||[];const active=versions[0],prior=versions[1];
      openSheet({title:'Compare decision versions',subtitle:'White-box version lineage',body:`<div class="compare-grid"><div><span class="chip amber">${esc(prior?.version||'v3.0')}</span><h4>${esc(prior?.rule_text||detail.decision.supersedes||'Payslips-only rule')}</h4><p>Historical / superseded instruction.</p></div><div><span class="chip green">${esc(active?.version||detail.decision.version)}</span><h4>${esc(active?.rule_text||detail.decision.approved_rule)}</h4><p>Current governed decision.</p></div></div>`});return;
    }
    if(action==='approve'){openSheet({title:'Approval provenance',subtitle:`${detail.decision.decision_ref} is human-governed`,body:`<div class="sheet-section"><span class="chip green">APPROVED</span><h4 style="margin-top:14px">${esc(detail.decision.approved_rule)}</h4><dl class="sheet-kv"><dt>Approved by</dt><dd>${esc(detail.decision.approved_by)}</dd><dt>Effective</dt><dd>${esc(detail.decision.effective_at||'')}</dd><dt>Source approval</dt><dd>${esc(detail.decision.source_approval_ref||'')}</dd><dt>Current version</dt><dd>${esc(detail.decision.version)}</dd></dl></div>`});return;}
    if(action==='merge'){try{const p=await api(`/assurance/proof-pack?conflict_ref=${encodeURIComponent(selectedConflictObj()?.conflict_ref||'CF-INCOME-001')}`);openSheet({title:'Merge proof',subtitle:'Evidence → governed decision',body:`<div class="sheet-section"><span class="chip green">CANONICAL MERGE VERIFIED</span><h4 style="margin-top:14px">${esc(detail.decision.decision_ref)} is linked to evidence, reasoning, impact and ledger proof.</h4><p>Merge does not overwrite history. It establishes the approved decision as the current canonical version while superseded evidence remains traceable.</p><dl class="sheet-kv"><dt>Evidence sources</dt><dd>${p.evidence?.sources?.length||'linked'}</dd><dt>Blast radius</dt><dd>${p.impact?.affected_cases||27} cases</dd><dt>Ledger</dt><dd>${p.ledger?.verified?'VERIFIED':'CHECK'}</dd><dt>Proof</dt><dd class="mono">${esc(shortHash(p.proof?.bundle_digest))}</dd></dl></div>`});}catch(e){status(e.message,'error');}return;}
    if(action==='rollback'||action==='restore'){try{const alerts=await api('/bodyguard/alerts');const a=alerts[0];if(action==='restore'&&a&&a.status!=='restored'){await api(`/bodyguard/alerts/${a.alert_ref}/restore`,{method:'POST',body:'{}'});status('Approved version restored','ok');await openLedgerCapability();return;}closeSheet();await openBodyguardCapability();if(!a)status('Simulate a protected overwrite to demonstrate rollback','info',3200);}catch(e){status(e.message,'error');}return;}
  }

  async function downloadLedger(){
    try{const r=await fetch('/api/ledger/export.csv',{headers:{Authorization:`Bearer ${state.token}`}});if(!r.ok)throw new Error(`Ledger export failed (${r.status})`);const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='juristwin_decision_ledger.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);status('Ledger exported','ok');}catch(e){status(e.message,'error',3000);}
  }

  function bodyguardAlertMarkup(a){
    const timeline=(a.timeline||[]).map(t=>`<div class="bodyguard-tick ${esc(t.status||'')}"><i></i><div><b>${esc(t.action)}</b><small>${esc(t.time||'pending')}${t.detail?` · ${esc(t.detail)}`:''}</small></div></div>`).join('');
    return `<section class="bodyguard-alert"><div class="bodyguard-alert-head"><div><span class="chip red">${esc(a.severity)} RISK</span><h3>${esc(a.title)}</h3></div><span class="chip amber">${esc(cap(a.status))}</span></div><dl class="sheet-kv"><dt>User</dt><dd>${esc(a.user_ref)}</dd><dt>Document</dt><dd>${esc(a.document)}</dd><dt>Action</dt><dd>${esc(a.action)}</dd><dt>Conflict</dt><dd>${esc(a.conflict_decision_ref)}</dd></dl><div class="bodyguard-timeline">${timeline}</div><div class="feature-actions bodyguard-actions"><button class="btn" data-bodyguard-action="review" data-alert="${esc(a.alert_ref)}">Review activity</button><button class="btn danger" data-bodyguard-action="revoke-access" data-alert="${esc(a.alert_ref)}">Revoke access</button><button class="btn" data-bodyguard-action="escalate" data-alert="${esc(a.alert_ref)}">Escalate</button><button class="btn" data-bodyguard-action="authorize-overwrite" data-alert="${esc(a.alert_ref)}">Authorise overwrite</button><button class="btn primary" data-bodyguard-action="restore" data-alert="${esc(a.alert_ref)}">Restore version</button><button class="btn quiet" data-bodyguard-action="explain" data-alert="${esc(a.alert_ref)}">Explain why</button></div></section>`;
  }

  async function openBodyguardCapability(){
    const alerts=await api('/bodyguard/alerts');const a=alerts[0];
    openSheet({title:'Decision Protection',subtitle:'Keep an approved decision safe after publication',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">AFTER APPROVAL</span><h3>JurisTwin keeps watching for unsafe changes.</h3><p>If someone tries to change a protected decision or access it inappropriately, the system records the event and gives an authorised operator clear response options.</p></div>${a?bodyguardAlertMarkup(a):'<div class="feature-empty bodyguard-empty"><b>No active security incident.</b><br>Publish the flagship decision, then use the demo button below to show what happens if someone tries an unsafe change.</div>'}<div class="feature-actions"><button class="btn danger" id="simulateBodyguard">Simulate unsafe policy change</button><button class="btn" id="openDecisionLedger">View decision history</button></div><!-- AI Bodyguard + Decision Ledger -->`,onOpen:()=>{$('#simulateBodyguard')?.addEventListener('click',async()=>{try{const x=await api('/bodyguard/simulate-attack',{method:'POST',body:'{}'});status(`Unsafe change contained · ${x.alert_ref}`,'ok');await openBodyguardCapability();}catch(e){status(e.message,'error',3200);}});$('#openDecisionLedger')?.addEventListener('click',openLedgerCapability);$$('[data-bodyguard-action]',portal).forEach(b=>b.addEventListener('click',()=>runBodyguardAction(b.dataset.alert,b.dataset.bodyguardAction)));}});
  }

  async function runBodyguardAction(ref,action){
    try{
      if(action==='explain'){const x=await api(`/bodyguard/alerts/${ref}/explain`,{method:'POST',body:'{}'});openSheet({title:'Why Bodyguard intervened',subtitle:x.decision_version||'Governed decision',body:`<div class="platform-intro compact"><h3>${esc(x.summary)}</h3></div><div class="feature-list">${x.reasons.map(r=>`<div class="feature-row"><span class="ledger-dot danger-dot"></span><div><b>Governance signal</b><small>${esc(r)}</small></div></div>`).join('')}</div>`});return;}
      const path=action==='authorize-overwrite'?`/bodyguard/alerts/${ref}/authorize-overwrite`:`/bodyguard/alerts/${ref}/${action}`;
      const body=action==='authorize-overwrite'?JSON.stringify({comments:'Authorised through JurisTwin governed operator workflow'}):'{}';
      await api(path,{method:'POST',body});status(`${cap(action)} completed`,'ok');await refreshCore();await openBodyguardCapability();
    }catch(e){status(e.message,'error',3200);}
  }

  async function openIntegrationsCapability(){
    const items=await api('/integrations');
    openSheet({title:'Live Source Connections',subtitle:'Which workplace systems are feeding JurisTwin?',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">KEEP THE ANSWER CURRENT</span><h3>Approved sources can update without changing the privacy rules.</h3><p>Each connected source shows its current status and data volume. Source access is still controlled separately in Privacy & Security.</p></div><div class="connector-source-band"><span>Outlook</span><span>Teams</span><span>Gmail</span><span>SharePoint</span><span>ClickUp</span><span>Customer System</span><span>Policy documents</span></div><div class="integration-grid">${items.map(i=>`<div class="integration-card"><div><b>${esc(i.name)}</b><small>${fmt(i.object_count)} ${esc(i.details?.metric||'items')} available</small></div><span class="chip ${i.status==='connected'?'green':'amber'}">${i.status==='connected'?'CONNECTED':esc(i.status)}</span><em>${esc(i.details?.adapter_mode==='live_http_ingress'?'Live machine updates':(i.last_sync_label||'Ready for demo'))}</em>${i.details?.adapter_mode==='deterministic_finals_adapter'?`<button class="btn integration-action" data-adapter-info="${esc(i.key)}">Connection details</button>`:i.details?.adapter_mode==='live_http_ingress'?`<button class="btn integration-action" data-live-ingress="${esc(i.key)}">Live-update details</button>`:`<button class="btn integration-action" data-integration="${esc(i.key)}" data-status="${esc(i.status)}">${i.status==='connected'?'Refresh source':'Connect source'}</button>`}</div>`).join('')}</div><div class="webhook-proof manager-webhook"><div><span class="eyebrow">LIVE UPDATE PROTECTION</span><h4>New machine updates are checked before acceptance.</h4><p>The demo includes a signed live-update path so unseen evidence can enter the same workflow without bypassing security.</p></div><button class="btn" id="webhookDetails">Technical details</button></div>`,onOpen:()=>{$$('[data-integration]',portal).forEach(b=>b.addEventListener('click',async()=>{try{const key=b.dataset.integration;const connected=b.dataset.status==='connected';await api(`/integrations/${key}/${connected?'sync':'connect'}`,{method:'POST',body:connected?'{}':JSON.stringify({config:{demo:true}})});status(`${key} ${connected?'refreshed':'connected'}`,'ok');await openIntegrationsCapability();}catch(e){status(e.message,'error',3000);}}));$$('[data-live-ingress]',portal).forEach(b=>b.addEventListener('click',showWebhookProof));$$('[data-adapter-info]',portal).forEach(b=>b.addEventListener('click',()=>openSheet({title:'Demo source connection',subtitle:'How this source is represented in the finals environment',body:`<div class="sheet-section"><span class="chip amber">DEMO DATA</span><h4 style="margin-top:14px">This source uses a deterministic local dataset rather than a live corporate tenant.</h4><p>The separate signed live-update path proves that unseen evidence can enter over HTTP and be checked by the same decision workflow.</p><button class="btn primary" id="adapterWebhook">Show live-update proof</button></div>`,onOpen:()=>$('#adapterWebhook')?.addEventListener('click',showWebhookProof)})));$('#webhookDetails')?.addEventListener('click',showWebhookProof);}});
  }

  function showWebhookProof(){openSheet({title:'Signed webhook proof',subtitle:'Real HTTP ingress, authenticated locally',body:`<div class="sheet-section"><span class="chip green">HMAC-SHA256</span><h4 style="margin-top:14px">External event → signature verify → replay guard → policy reasoner → blast radius → ledger.</h4><p>This is a real machine-to-machine connector contract. It does not depend on external cloud credentials during finals.</p><dl class="sheet-kv"><dt>Endpoint</dt><dd class="mono">POST /api/live/webhook</dd><dt>Authentication</dt><dd>HMAC-SHA256</dd><dt>Replay defence</dt><dd>event_id idempotency</dd><dt>Demo command</dt><dd class="mono">backend\\.venv\\Scripts\\python.exe backend\\scripts\\send_live_webhook.py</dd></dl></div>`});}

  function openReasonerCapability(){
    const d=state.lastChallenge,reason=d?.analysis?.policy_atoms?.reasoning||{},collisions=reason.collisions||[],hybrid=d?.analysis?.hybrid_ai||{},learned=hybrid.learned||{},arb=hybrid.arbitration||{},consensus=hybrid.governed_consensus||{};
    openSheet({title:'Hybrid AI Policy Reasoner',subtitle:'Learned proposal + white-box verification',wide:true,body:d?`<div class="platform-intro compact"><span class="eyebrow">MEASURED AI + STRUCTURED REASONING</span><h3>${esc(d.verdict)} · ${Math.round(Number(d.confidence||0)*100)}% confidence</h3><p>A trained local NLP classifier proposes the policy domain and stance. JurisTwin then cross-checks the proposal against symbolic policy atoms, authority and explicit collision rules. Disagreement abstains instead of inventing certainty.</p></div><div class="reasoner-grid">${collisions.map(c=>`<div class="reasoner-collision"><div><small>CANONICAL</small><b>${esc(c.object||'POLICY')} · ${esc(c.canonical_modality||'')}</b></div><span>↔</span><div><small>INCOMING</small><b>${esc(c.object||'POLICY')} · ${esc(c.incoming_modality||'')}</b></div><p>${esc(c.explanation||'Explicit policy collision detected.')}</p></div>`).join('')||'<div class="feature-empty">No explicit symbolic collision in the latest challenge.</div>'}</div><div class="sheet-section"><dl class="sheet-kv"><dt>Learned engine</dt><dd>${esc(learned.engine||'JurisTwin Hybrid Policy Intelligence')}</dd><dt>Learned domain</dt><dd>${esc(learned.domain?.label||'—')} · ${Math.round(Number(learned.domain?.confidence||0)*100)}%</dd><dt>Learned stance</dt><dd>${esc(learned.stance?.label||'—')} · ${Math.round(Number(learned.stance?.confidence||0)*100)}%</dd><dt>Arbitration</dt><dd>${esc(arb.engine||'Sentinel Dual-Control Consensus')} · ${esc(arb.abstained?'ABSTAINED':arb.domain_source||'verified')}</dd><dt>Authority-weighted consensus</dt><dd>${fmt(consensus.score||0)}/100 · learned + symbolic + authority + semantic agreement</dd><dt>Model authority</dt><dd>Cannot publish or canonicalise evidence</dd></dl></div><div class="feature-actions"><button class="btn" id="reasonerModel">AI model card</button><button class="btn primary" id="reasonerEvidence">Open Evidence Lab</button></div>`:`<div class="feature-empty"><b>No live policy challenge yet.</b><br>Give JurisTwin unseen evidence first, then return here to inspect learned predictions and extracted atoms.</div><div class="feature-actions"><button class="btn" id="reasonerModel">AI model card</button><button class="btn primary" id="reasonerEvidence">Challenge Sentinel</button></div>`,onOpen:()=>{$('#reasonerEvidence')?.addEventListener('click',()=>{closeSheet();navigate('evidence',()=>setTimeout(()=>$('#challengeBody')?.focus(),80));});$('#reasonerModel')?.addEventListener('click',showAIModelCard);}});
  }

  async function showRolloutPlan(){
    const c=selectedConflictObj(); if(!c){status('Select a conflict first','error');return;}
    const d=await api(`/assurance/rollout-plan/${encodeURIComponent(c.conflict_ref)}`);
    openSheet({title:'Progressive rollout',subtitle:`${c.name} · safe delivery`,wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">SAFE DELIVERY</span><h3>CANARY → CONTROLLED → FULL</h3><p>${d.affected_cases} affected cases are deterministically assigned to rollout waves. Rollback conditions remain visible before deployment.</p></div><div class="rollout-waves">${d.waves.map(w=>`<article><span class="chip ${w.name==='CANARY'?'amber':w.name==='FULL'?'green':'cyan'}">${esc(w.name)}</span><b>${w.case_count}</b><small>${esc(w.entry_criteria||'governed cohort')}</small></article>`).join('')}</div><div class="sheet-section"><h4>Rollback conditions</h4><div class="compact-tags">${[...new Set((d.waves||[]).map(x=>x.rollback_trigger).filter(Boolean))].map(x=>`<span>${esc(x)}</span>`).join('')}</div></div>`});
  }

  async function showDecisionReplay(){
    const c=selectedConflictObj();
    try{
      const detail=await decisionForConflict(c);
      if(!detail?.decision)throw new Error('Decision not published');
      const ref=detail.decision.decision_ref; const d=await api(`/assurance/replay/${encodeURIComponent(ref)}`);
      openSheet({title:'Decision Replay',subtitle:`Reconstruct ${ref} from evidence to propagation`,wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">DECISION TIME MACHINE</span><h3>${esc(d.current?.version||ref)} · ${esc(d.status)}</h3><p>The current decision can be reconstructed from version history and the tamper-evident ledger.</p></div><div class="replay-timeline">${(d.timeline||[]).map(x=>`<div class="replay-step"><i></i><div><b>${esc(x.label)}</b><small>${esc(x.actor||'system')} · ${esc(x.at||'')}</small></div></div>`).join('')}</div><div class="feature-actions"><button class="btn primary" id="replayLedger">Open ledger</button></div>`,onOpen:()=>$('#replayLedger')?.addEventListener('click',openLedgerCapability)});
    }catch(e){
      openSheet({title:'Decision Replay',subtitle:`Publish ${c?.name||'the selected conflict'} first`,body:`<div class="feature-empty"><b>The time machine starts after governance.</b><br>Run the selected Digital Twin and publish Option C, then replay the decision history.</div><div class="feature-actions"><button class="btn primary" id="replayTwin">Go to Digital Twin</button></div>`,onOpen:()=>$('#replayTwin')?.addEventListener('click',()=>{closeSheet();navigate('twin');})});
    }
  }

  async function finalFlowMenu(){
    let story={steps:[],operating_impact:{}},demo={};try{[story,demo]=await Promise.all([api('/demo/story'),api('/demo/status')]);}catch{}
    const published=!!demo.decision_published;
    const done=(key)=>key==='CONNECT'||key==='EXPOSE'||((key==='SIMULATE'||key==='RECOMMEND')&&(!!state.sim||published))||(key==='APPROVE'&&published)||(key==='PROTECT'&&published);
    const labels={CONNECT:'Find sources',EXPOSE:'Spot issue',SIMULATE:'Compare options',RECOMMEND:'Choose response',APPROVE:'Approve',PROTECT:'Protect'};
    const impact=story.operating_impact||{applications_affected:27,rejected_cases_flagged:1,qa_tests_updated:8,documents_superseded:3,officers_notified:4};
    openSheet({title:'Demo Flow',subtitle:'From a business question to a protected decision',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">ONE CONTINUOUS MANAGEMENT STORY</span><h3>${published?'The decision is approved, updated and protected.':'Six simple steps from uncertainty to action.'}</h3><p>Click any step to jump directly to that part of the live system.</p></div><div class="final-flow manager-flow">${(story.steps||[]).map(x=>`<button class="flow-step ${done(x.key)?'done':''}" data-flow-step="${esc(x.key)}"><i>${x.step}</i><b>${esc(labels[x.key]||cap(x.key))}</b><span>${esc(x.action)}</span></button>`).join('')}</div><div class="operating-impact"><div><b>${impact.applications_affected}</b><span>customer applications affected</span></div><div><b>${impact.rejected_cases_flagged}</b><span>case flagged for review</span></div><div><b>${impact.qa_tests_updated}</b><span>quality checks updated</span></div><div><b>${impact.documents_superseded}</b><span>documents replaced</span></div><div><b>${impact.officers_notified}</b><span>staff notified</span></div></div><div class="flow-thesis">Find the answer. <b>Compare the response.</b> Approve it safely. Keep the proof.</div>`,onOpen:()=>$$('[data-flow-step]',portal).forEach(b=>b.addEventListener('click',()=>runFlowStep(b.dataset.flowStep)))});
  }

  async function runFlowStep(key){
    closeSheet();
    if(key==='CONNECT'){await openMemoryCapability();return;}
    if(key==='EXPOSE'){navigate('conflict');return;}
    if(key==='SIMULATE'){navigate('twin',()=>setTimeout(()=>{if(!state.sim)runTwin();},80));return;}
    if(key==='RECOMMEND'){navigate('twin');return;}
    if(key==='APPROVE'){if(state.sim){setTimeout(openGovernance,50);}else{navigate('twin',()=>setTimeout(runTwin,80));}return;}
    if(key==='PROTECT'){await openBodyguardCapability();return;}
  }

  function showPositioning(){openSheet({title:'Not another enterprise chatbot',subtitle:'Decision intelligence, not answer generation',wide:true,body:`<div class="positioning-pairs"><div><small>CHATBOTS</small><b>Answer.</b><span>SENTINEL</span><strong>Governs.</strong></div><div><small>CHATBOTS</small><b>Retrieve.</b><span>SENTINEL</span><strong>Verifies.</strong></div><div><small>CHATBOTS</small><b>Summarise.</b><span>SENTINEL</span><strong>Simulates.</strong></div></div><div class="positioning-wedge"><span class="eyebrow">THE WEDGE</span><h3>Decision memory + explainable simulation + governance ledger in one loop.</h3><p>Others retrieve knowledge. JurisTwin turns conflicting evidence into safe, testable, governed decisions.</p></div>`});}

  function showPilotScale(){openSheet({title:'Built for a pilot. Designed to scale.',subtitle:'Pitch-deck commercial path + truthful finals runtime',wide:true,body:`<div class="pilot-grid"><article><span class="eyebrow">PILOT TARGETS</span><ul><li><b>50%</b> faster case investigation</li><li><b>30%</b> fewer duplicate requests</li><li><b>60%</b> faster access to approved decisions</li><li><b>100%</b> evidence-linked final decisions</li><li><b>Zero</b> restricted-data exposure target</li></ul></article><article><span class="eyebrow">FEASIBLE MVP</span><ul><li>1 customer case</li><li>3 employee roles</li><li>1 decision conflict</li><li>3 simulated actions</li><li>1 security incident</li><li>1 version-controlled decision</li></ul></article><article><span class="eyebrow">COMMERCIAL PATH</span><ul><li>JurisTech internal pilot</li><li>Existing banking clients</li><li>Insurance + regulated enterprises</li><li>Enterprise licence</li><li>Implementation fee</li><li>Governance services</li></ul></article></div><div class="runtime-truth"><div><b>Verified finals runtime</b><span>Zero-build SPA · FastAPI · SQLAlchemy · local learned NLP + symbolic reasoner · SQLite/PostgreSQL compatibility · RBAC</span></div><div><b>Pilot target architecture shown in deck</b><span>React · FastAPI · ChromaDB (pilot target) · PostgreSQL · Interpretable ML · RBAC</span></div></div>`});}

  function workspaceMenu(){
    openSheet({title:'Workspace settings',subtitle:'Demo and display controls',body:`
      <div class="sheet-section"><h4>Presentation mode</h4><p>Make supporting text larger for a projector or meeting-room display.</p><div style="margin-top:14px"><button class="btn ${state.presentation?'primary':''}" id="presentationToggle">${state.presentation?'Presentation mode ON':'Turn on presentation mode'}</button></div></div>
      <div class="sheet-section"><h4>Reset demo</h4><p>Return the demo data to the starting scenario without restarting the server.</p><div style="margin-top:12px"><button class="btn" id="sheetReset">${icon('reset',14)} Reset demo scenario</button></div></div>
      <details class="technical-details"><summary>Keyboard shortcuts</summary><dl class="sheet-kv"><dt>Alt + J</dt><dd>Test new evidence</dd><dt>Alt + C</dt><dd>Why sources disagree</dd><dt>Alt + T</dt><dd>Compare solutions</dd><dt>Alt + A</dt><dd>Safe to publish?</dd><dt>Alt + G</dt><dd>Privacy & Security</dd><dt>Alt + P</dt><dd>Presentation mode</dd><dt>Alt + F</dt><dd>Demo Flow</dd></dl></details>
      <div class="sheet-section"><button class="btn danger" id="sheetLogout">${icon('logout',14)} Sign out</button></div>`,onOpen:()=>{$('#presentationToggle')?.addEventListener('click',togglePresentation); $('#sheetReset')?.addEventListener('click',resetDemo); $('#sheetLogout')?.addEventListener('click',()=>logout(true));}});
  }

  function togglePresentation(){
    state.presentation=!state.presentation;
    storage.set('jt_presentation',state.presentation?'1':'0');
    closeSheet();
    renderShell();
    status(state.presentation?'Presentation mode enabled':'Presentation mode disabled','ok');
  }

  async function resetDemo(){
    try {
      status('Resetting finals scenario…');
      await api('/demo/reset',{method:'POST',body:'{}'});
      closeSheet(); state.sim=null; state.lastChallenge=null; state.overviewAnswer=null; state.overviewRole='manager'; state.selectedOption='C'; state.graphPositions={}; state.assurance=null; state.readiness=null; state.security=null; state.managerControls=null; state.decisionRefs={}; await refreshCore(); renderShell(); status('Finals scenario restored','ok');
    } catch(e) { status(e.message,'error',3200); }
  }

  function logout(show=true){
    state.token=''; state.user=null; storage.remove('jt_token'); stopHealthPulse(); closeSheet(); if(show) status('Signed out'); renderLogin();
  }

  async function refreshCore(){
    const [dashboard,conflicts,managerControls] = await Promise.all([api('/dashboard'),api('/conflicts'),api('/system/manager-control-summary')]); state.dashboard=dashboard; state.conflicts=conflicts; state.managerControls=managerControls;
  }

  function renderSkeleton(){
    return `<div class="loading-page"><div class="skeleton" style="height:38px;width:42%;border-radius:10px"></div><div class="skeleton" style="height:14px;width:54%;border-radius:7px;margin-top:12px"></div><div class="skeleton" style="height:72px;border-radius:14px;margin-top:28px"></div><div class="skeleton" style="height:360px;border-radius:18px;margin-top:14px"></div></div>`;
  }

  function renderPage(){
    if (state.page==='controls') return renderManagementControls();
    if (state.page==='conflict') return renderConflict();
    if (state.page==='twin') return renderTwin();
    if (state.page==='assurance') return renderAssurance();
    if (state.page==='evidence') return renderEvidence();
    if (state.page==='governance') return renderGovernance();
    return renderOverview();
  }

  function answerTone(statusValue){
    return (statusValue==='VERIFIED'||statusValue==='CONFLICT_PRESENT')?'verified':statusValue==='RESTRICTED'?'restricted':'review';
  }

  function answerChip(statusValue){
    return (statusValue==='VERIFIED'||statusValue==='CONFLICT_PRESENT')?'green':statusValue==='RESTRICTED'?'red':'cyan';
  }

  function managementStatus(r){
    const v=r?.management_status||r?.status||'REVIEW_REQUIRED';
    const map={VERIFIED:'ANSWER READY',CONFLICT_PRESENT:'ANSWER READY',RESTRICTED:'LIMITED BY ACCESS',REVIEW_REQUIRED:'REVIEW NEEDED',NEEDS_REVIEW:'REVIEW NEEDED'};
    return map[v]||String(v).replace(/_/g,' ');
  }

  function resolutionLabel(mode=''){
    const labels={DECISION_CONTRACT:'Approved decision',APPROVED_AUTHORITY:'Official source',HIGHEST_AUTHORITY:'Highest approved source',SAME_TIER_MAJORITY:'Majority at same approval level',MAJORITY_TIE_REVIEW:'Needs human review'};
    return labels[mode]||cap(mode||'Approved resolution');
  }


  function renderManagementControls(){
    const d=state.managerControls;
    if(!d)return `<div class="page"><section class="page-hero reveal"><div><span class="eyebrow">LECTURER FEEDBACK</span><h2>Feedback → working controls.</h2></div><div class="hero-actions"><button class="btn primary" id="refreshManagerControls">Check controls</button></div></section><section class="surface manager-empty reveal"><div><div class="empty-icon">${icon('shield',22)}</div><h3>Checking controls…</h3></div></section></div>`;
    const controls=d.controls||[];
    return `<div class="page controls-page compact-page">
      <section class="page-hero controls-hero reveal"><div><span class="eyebrow">LECTURER FEEDBACK</span><h2>Every recommendation is now visible in the system.</h2></div><div class="hero-actions"><span class="control-score ${d.status==='COMPLETE'?'complete':'review'}"><b>${Number(d.score||0)}</b><small>/100</small></span><button class="btn" id="refreshManagerControls">Re-check</button></div></section>
      <section class="surface controls-summary reveal"><div class="controls-summary-head"><div><h3>${fmt(d.passed)}/${fmt(d.total)} controls ready</h3></div><span class="chip green">${icon('check',11)} ${esc(d.status)}</span></div><div class="controls-principles"><span>${icon('check',14)} One answer</span><span>${icon('shield',14)} Approved sources</span><span>${icon('lock',14)} Private data blocked</span><span>${icon('check',14)} Role access</span><span>${icon('spark',14)} Live updates</span><span>${icon('file',14)} Audit trail</span></div></section>
      <section class="control-upgrade-grid reveal">${controls.map((c,i)=>`<article class="surface control-upgrade-card compact-control-card" title="${esc(c.manager_question||'')}"><div class="control-upgrade-top"><span class="control-number">${String(i+1).padStart(2,'0')}</span><span class="chip ${c.status==='PASS'?'green':'amber'}">${esc(c.status)}</span></div><h3>${esc(brief(c.title,52))}</h3><div class="before-after compact-before-after"><div class="before"><small>BEFORE</small><p>${esc(brief(c.original,72))}</p></div><div class="upgrade-arrow">→</div><div class="after"><small>NOW</small><p>${esc(brief(c.now,82))}</p></div></div><div class="control-proof"><span>${icon('check',14)}</span><div><small>LIVE</small><b>${esc(brief(c.proof||'Control is active',68))}</b></div></div><button class="btn control-open" data-control-page="${esc(c.page||'overview')}" data-control-key="${esc(c.key||'')}">${esc(c.action||'Open')} ${icon('arrow',12)}</button></article>`).join('')}</section>
      <section class="surface manager-demo-path reveal compact-demo-path"><div><span class="eyebrow">DEMO FLOW</span><h3>Answer → Privacy → Export → Audit → Live update</h3></div><div class="demo-path-pills"><button data-demo-page="overview">1 · Answer</button><button data-demo-page="governance">2 · Privacy</button><button data-demo-page="governance">3 · Export</button><button data-demo-page="governance">4 · Audit</button><button data-demo-page="evidence">5 · Live</button></div></section>
    </div>`;
  }

  async function loadManagerControls(showStatus=true){
    try{
      if(showStatus)status('Re-checking management controls…');
      state.managerControls=await api('/system/manager-control-summary');
      if(state.page==='controls')renderShell();
      if(showStatus)status(`${state.managerControls.passed}/${state.managerControls.total} management controls ready`,'ok');
    }catch(e){status(e.message,'error',3200);}
  }

  function sourceRelationLabel(x){
    const r=(x.relation||'context').toLowerCase();
    if(r==='approved')return 'GOVERNED';
    if(r==='conflict')return 'CONFLICTING';
    if(r==='outdated')return 'OUTDATED';
    if(r==='informal')return 'INFORMAL';
    if(r==='operational')return 'CUSTOMER IMPACT';
    return cap(r);
  }

  function sourceRelationClass(x){
    const r=(x.relation||'context').toLowerCase();
    return r==='approved'?'green':(r==='conflict'||r==='outdated')?'red':r==='informal'?'amber':r==='operational'?'cyan':'';
  }

  function sourceMixMarkup(r,limit=4){
    const rows=(r?.source_mix||[]).slice(0,limit);
    if(!rows.length)return '';
    return `<div class="source-mix"><div class="source-mix-head"><b>What JurisTwin checked · eligible sources</b><span>${fmt(r.synthesis?.sources_considered||rows.length)} privacy-scoped · role-filtered</span></div><div class="source-mix-grid">${rows.map(x=>`<article class="source-proof ${x.redacted?'redacted':''}"><div class="source-proof-top"><span class="chip ${sourceRelationClass(x)}">${esc(sourceRelationLabel(x))}</span><small>${esc(x.source||'Evidence')} · ${esc(x.version||'current')}</small></div><b>${esc(x.title||x.source||'Governed evidence')}</b><p>${esc(x.redacted?'Restricted content hidden for this role.':(x.message||'').slice(0,190))}</p><footer>${esc(x.authority||'Governed source')}</footer></article>`).join('')}</div></div>`;
  }

  function overviewAnswerMarkup(){
    const r=state.overviewAnswer;
    if(!r)return `<div class="overview-answer-placeholder manager-placeholder compact-placeholder"><div><b>Ask a question. Get one answer + source.</b></div><div class="source-mini-row"><span>${icon('check',12)} Official email</span><span>${icon('check',12)} Approved Teams</span><span>${icon('check',12)} Policies</span><span>${icon('lock',12)} DMs blocked</span></div></div>`;
    const res=r.resolution||{}, fresh=r.freshness||{}, sources=r.sources_used||r.citations||[];
    const primary=r.primary_source||sources[0]||{};
    const excluded=Number(res.excluded_count||0);
    return `<div class="overview-answer-result ${answerTone(r.status)} manager-answer compact-answer">
      <div class="overview-answer-status"><span class="chip ${answerChip(r.status)}">${esc(managementStatus(r))}</span><span>${esc(cap(r.role||state.overviewRole))} view</span></div>
      <div class="definitive-answer"><small>ANSWER</small><h3>${esc(r.answer||'')}</h3></div>
      ${r.warning?`<p class="answer-warning subtle">${esc(brief(r.warning,120))}</p>`:''}
      <div class="manager-proof-grid compact-proof-grid">
        <article class="primary-proof"><div class="manager-proof-icon">${icon('check',16)}</div><small>SOURCE</small><b>${esc(primary.title||r.source||'Approved source')}</b><span>${esc(primary.source||r.source||'Enterprise source')}</span></article>
        <article><div class="manager-proof-icon">${icon('shield',16)}</div><small>WHY</small><b>${esc(resolutionLabel(res.mode))}</b><span>${esc(brief(res.explanation||'Highest approved source wins.',72))}</span></article>
        <article><div class="manager-proof-icon">${icon('lock',16)}</div><small>PRIVACY</small><b>${fmt(res.eligible_count||sources.length)} used · ${fmt(excluded)} blocked</b><span>Private/casual sources excluded</span></article>
        <article><div class="manager-proof-icon">${icon('spark',16)}</div><small>FRESHNESS</small><b>${fresh.answer_recomputed?'Checked now':'Current'}</b><span>Latest approved state</span></article>
      </div>
      <div class="main-source-lineage compact-lineage"><div class="source-mix-head"><b>Sources used</b><span>${sources.length} total</span></div>${sources.length?sources.slice(0,2).map((x,i)=>`<div class="main-source-row"><i>${i+1}</i><div><b>${esc(x.title||x.source||'Approved evidence')}</b><span>${esc(x.source||'Evidence')} · ${esc(x.version||'current')}</span></div><span class="chip ${i===0?'green':''}">${i===0?'MAIN':'SUPPORT'}</span></div>`).join(''):'<div class="feature-empty">No source visible for this role.</div>'}</div>
      <details class="technical-details compact-details"><summary>How was this answer chosen?</summary><p>${esc(brief(res.winner_rule||'Approved scope first. Highest authority wins. Majority is only used between equally authoritative sources.',180))}</p></details>
      <div class="answer-proof-row compact-actions"><span>${icon('shield',12)} Protected source selection</span><div><button class="btn quiet" id="overviewSourcePolicy">Source rules</button><button class="btn quiet" id="overviewAIProof">Technical</button><button class="btn quiet" id="overviewRefresh">Refresh</button></div></div>
    </div>`;
  }

  function showOverviewAIProof(){
    const r=state.overviewAnswer;if(!r)return;const a=r.ai_verification||{};
    openSheet({title:'How AI verified this answer',subtitle:'Measured learning + deterministic verification + zero model publication authority',body:`<div class="platform-intro compact"><span class="eyebrow">HYBRID AI · INSPECTABLE BY DESIGN</span><h3>Learned AI generalises. Symbolic reasoning verifies. Humans publish.</h3><p>The statistical model can route unfamiliar language, but it cannot create or publish governed policy.</p></div><div class="assurance-kpis"><div><b>${Math.round(Number(a.domain_macro_f1||0)*1000)/10}%</b><span>Domain Macro-F1</span></div><div><b>${Math.round(Number(a.stance_macro_f1||0)*1000)/10}%</b><span>Stance Macro-F1</span></div><div><b>${a.publication_authority??0}</b><span>Model publication authority</span></div></div><div class="plain-answer-grid"><div><small>LEARNED COMPONENT</small><p>${esc(a.architecture||'TF-IDF word + character features with Logistic Regression')}</p></div><div><small>DETERMINISTIC VERIFIER</small><p>${esc(a.symbolic_verifier||'Policy Atom Reasoner')} checks the policy collision before governance.</p></div><div><small>RESILIENCE</small><p>Internet required: <b>${a.internet_required?'Yes':'No'}</b>. Low-confidence or disagreement routes to review rather than fabricated certainty.</p></div><div><small>PUBLICATION CONTROL</small><p>${esc(a.decision_rule||'Learned model routes; symbolic reasoning verifies; human authority publishes.')}</p></div><div><small>CLIENT DATA TRAINING</small><p><b>Disabled.</b> Client evidence is used only for governed retrieval/indexing. It is not added to the classifier training corpus or sent to an external model.</p></div></div>`});
  }

  async function runOverviewAnswer(role=state.overviewRole){
    const input=$('#overviewQuestion');
    const q=(input?.value||state.overviewQuestion||'').trim();
    if(q.length<5){status('Ask a complete policy question','error');return;}
    state.overviewQuestion=q; state.overviewRole=role;
    const btn=$('#overviewAsk');if(btn){btn.disabled=true;btn.textContent='Checking…';}
    try{
      const r=await api('/memory/answer',{method:'POST',body:JSON.stringify({question:q,preview_role:role})});
      state.overviewAnswer=r; state.security=null; renderShell();
      status(`${managementStatus(r)} · ${fmt((r.sources_used||r.citations||[]).length)} source${(r.sources_used||r.citations||[]).length===1?'':'s'} used`,'ok',2800);
    }catch(e){status(e.message,'error',3200);if(btn){btn.disabled=false;btn.textContent='Ask JurisTwin';}}
  }

  function renderOverview(){
    const d=state.dashboard||{}, m=d.metrics||{}, i=d.integrity||{};
    const flagship = state.conflicts.find(c=>c.conflict_ref==='CF-INCOME-001') || state.conflicts[0] || {};
    const resolved = flagship.status === 'resolved';
    const focusCount=Number(flagship.affected_customers||27);
    return `<div class="page compact-page">
      <section class="page-hero track2-hero reveal"><div><span class="eyebrow">MANAGEMENT DECISION DESK</span><h2>${resolved?'One approved answer. Fully traceable.':'Ask. Get one answer. See the source.'}</h2></div><div class="hero-actions"><button class="btn" id="overviewControls">Controls</button><button class="btn" id="overviewGovernance">Privacy</button><button class="btn primary" id="openCritical">${resolved?'Review decision':'Main issue'} ${icon('arrow',13)}</button></div></section>
      <section class="surface track2-ask reveal" aria-label="Ask JurisTwin"><div class="track2-ask-head"><div><span class="eyebrow">ASK JURISTWIN</span><h3>What should my team follow?</h3></div><span class="chip green">${icon('shield',11)} PROTECTED</span></div><div class="track2-query"><div class="track2-input-wrap">${icon('spark',17)}<input id="overviewQuestion" value="${esc(state.overviewQuestion)}" aria-label="Ask JurisTwin a policy question"></div><button class="btn primary" id="overviewAsk">Get answer</button></div><div class="track2-role-row"><span>View as</span><button class="role-pill ${state.overviewRole==='manager'?'active':''}" data-overview-role="manager">Manager</button><button class="role-pill ${state.overviewRole==='intern'?'active':''}" data-overview-role="intern">Intern</button></div>${overviewAnswerMarkup()}</section>
      <section class="metric-strip reveal compact-metrics">${metricStrip('Active cases',m.active_cases,'live')}${metricStrip('Open issues',m.decision_conflicts,'need alignment','alert')}${metricStrip('People affected',m.customers_at_risk,'exposure','alert')}${metricStrip('Trust score',i.score,'/100','good')}</section>
      <section class="command-grid">
        <article class="surface focus-panel reveal"><div class="focus-top"><span class="chip ${resolved?'green':'red'}">${resolved?'RESOLVED':'NEEDS ATTENTION'}</span><span class="muted">${esc(flagship.conflict_ref||'CF-INCOME-001')}</span></div><h3>${esc(flagship.name||'Income-document eligibility')}</h3><p>${esc(brief(flagship.root_cause||'Approved bank-statement policy conflicts with stale payslip-only guidance.',110))}</p><div class="impact-line"><div><b>${fmt(focusCount)}</b><span>affected</span></div><div><b>${fmt(flagship.systems_affected||5)}</b><span>systems</span></div><div><b>${Math.round(Number(flagship.confidence||.942)*100)}%</b><span>confidence</span></div></div><button class="btn focus-cta" id="overviewTwin">${resolved?'Review':'Compare fixes'} ${icon('play',12)}</button><div class="story-rail six"><div class="story-step done">Find</div><div class="story-step done">Resolve</div><div class="story-step ${state.sim||resolved?'done':''}">Compare</div><div class="story-step ${state.sim||resolved?'done':''}">Choose</div><div class="story-step ${resolved?'done':''}">Approve</div><div class="story-step ${resolved?'done':''}">Audit</div></div></article>
        <aside class="surface integrity-panel reveal"><div class="integrity-head"><div class="integrity-title"><span class="eyebrow">TRUST</span><b>Can management rely on this?</b></div><span class="chip ${Number(i.score||0)>=90?'green':'amber'}">${Number(i.score||0)>=90?'HEALTHY':'REVIEW'}</span></div><div class="integrity-main"><div class="integrity-gauge" style="--score:${Number(i.score||0)}" aria-label="Decision integrity ${Number(i.score||0)} out of 100"><div class="integrity-gauge-inner"><strong>${Number(i.score||0)}</strong><span>/100</span></div></div><div class="integrity-bars">${bar('Sources',i.evidence_alignment)}${bar('Versions',i.version_consistency)}${bar('Access',i.access_compliance)}${bar('Updates',i.decision_propagation)}</div></div><div class="integrity-foot"><span>${Number(i.score||0)>=90?'Trust checks aligned.':'Review a trust check.'}</span><button class="btn quiet integrity-flow-btn" id="overviewPlatform">Details ${icon('arrow',12)}</button></div></aside>
      </section>
      <section class="priority-list reveal"><div class="section-title"><div><span class="eyebrow">OTHER LIVE ISSUES</span><h3>What else needs attention?</h3></div></div><div class="priority-grid">${state.conflicts.filter(c=>c.conflict_ref!=='CF-INCOME-001').map(c=>`<button class="priority-card" data-open-conflict="${esc(c.conflict_ref)}"><div class="priority-card-top"><div class="priority-status"><span class="severity-dot ${String(c.severity||'medium').toLowerCase()}"></span><span>${esc(c.status==='resolved'?'Resolved':cap(c.severity||'Live'))}</span></div><span class="priority-ref">${esc(c.conflict_ref)}</span></div><div class="priority-copy"><b>${esc(c.name)}</b><p>${esc(brief(c.root_cause,72))}</p></div><div class="priority-foot"><span class="priority-impact"><strong>${fmt(c.affected_customers)}</strong><small>affected</small></span><span class="priority-open">Review ${icon('arrow',13)}</span></div></button>`).join('')}</div></section>
    </div>`;
  }

  function metricStrip(label,value,note,cls=''){ return `<div class="metric ${cls}"><div class="metric-label">${esc(label)}</div><div class="metric-value">${fmt(value)}</div><div class="metric-note">${esc(note)}</div></div>`; }
  function bar(label,value){ const v=clamp(Number(value||0),0,100); return `<div class="bar-row"><div class="bar-top"><span>${esc(label)}</span><b>${Math.round(v)}%</b></div><div class="bar-track"><i style="width:${v}%"></i></div></div>`; }

  function renderConflict(){
    const conflicts=state.conflicts||[];const c=conflicts.find(x=>x.conflict_ref===state.selectedConflict)||conflicts[0];
    if(!c) return `<div class="page"><div class="page-hero"><div><h2>No issue right now.</h2><p>Approved sources agree.</p></div></div></div>`;
    state.selectedConflict=c.conflict_ref; state.graph=c.graph;if(!state.selectedNode||!c.graph?.nodes?.some(n=>n.id===state.selectedNode))state.selectedNode=c.graph?.nodes?.find(n=>n.type==='rule')?.id||c.graph?.nodes?.[0]?.id;
    const plain=c.plain_explanation||{}, canonical=plain.canonical||{}, opposing=(plain.conflicting_evidence||[]), primary=opposing[0]||{};
    const extra=opposing.slice(1).map(x=>x.source).filter(Boolean);
    return `<div class="page compact-page"><section class="page-hero reveal"><div><div style="display:flex;gap:8px;align-items:center;margin-bottom:10px"><span class="chip ${String(c.severity).toLowerCase()==='critical'?'red':'amber'}">${esc(c.severity)}</span><span class="muted">${esc(c.conflict_ref)}</span></div><h2>Why are answers different?</h2><p>${esc(brief(plain.headline||c.root_cause,100))}</p></div><div class="hero-actions"><button class="btn" id="conflictProof">Audit proof</button><button class="btn primary" id="conflictTwin">Compare fixes ${icon('arrow',13)}</button></div></section><section class="surface conflict-plain reveal"><div class="plain-section-head"><div><span class="eyebrow">THE CONFLICT</span><h3>${esc(brief(plain.what_conflicts||plain.headline||'Two instructions disagree.',86))}</h3></div><button class="btn quiet" id="conflictMessages">All sources</button></div><div class="message-vs compact-message-vs"><article class="message-proof approved"><div class="message-source"><span class="chip green">FOLLOW</span><b>${esc(canonical.source||'Approved source')}</b><small>${esc(canonical.authority||'Approved owner')}</small></div><blockquote>“${esc(brief(canonical.message||'Approved governed rule',145))}”</blockquote></article><div class="vs-mark">VS</div><article class="message-proof conflict"><div class="message-source"><span class="chip red">CONFLICTS</span><b>${esc(primary.source||'Other source')}</b><small>${esc(primary.authority||'Operational guidance')}</small></div><blockquote>“${esc(brief(primary.message||'Conflicting instruction',145))}”</blockquote></article></div>${extra.length?`<div class="also-conflicts"><b>Also:</b> ${extra.slice(0,3).map(esc).join(' · ')}</div>`:''}<div class="manager-decision-summary compact-decision-summary"><article><small>STAFF SHOULD FOLLOW</small><b>${esc(canonical.source||'Approved source')}</b><p>${esc(brief(plain.why_canonical_wins||'Highest approved authority wins.',78))}</p></article><article><small>IMPACT</small><b>${fmt(c.affected_customers)} customers</b><p>${esc(brief(plain.why_it_matters||'Inconsistent treatment may occur.',78))}</p></article></div></section><div class="graph-section-title reveal"><div><span class="eyebrow">OPTIONAL SOURCE MAP</span><h3>See the evidence trail.</h3></div></div><div class="graph-legend reveal"><span class="green-dot">Official</span><span class="amber-dot">Informal</span><span class="red-dot">Conflict</span><span class="cyan-dot">Impact</span></div><section class="graph-shell reveal"><div class="graph-main"><div class="graph-toolbar"><div class="graph-tabs">${conflicts.map(x=>`<button type="button" class="graph-tab ${x.conflict_ref===c.conflict_ref?'active':''}" data-conflict="${esc(x.conflict_ref)}">${esc(x.name)}</button>`).join('')}</div><div class="graph-actions"><button type="button" class="graph-action" id="focusRoot" title="Focus official rule">${icon('target',14)}</button><button type="button" class="graph-action" id="fitGraph" title="Reset graph">${icon('fit',14)}</button></div></div><div class="graph-viewport"><svg id="graphSvg" class="graph-svg" viewBox="0 0 1000 620" preserveAspectRatio="xMidYMid meet" aria-label="Interactive evidence network"></svg></div></div><aside class="graph-inspector"><div class="inspector-label">Selected source</div><div id="nodeInspector"></div><div class="drag-hint"><b>Drag or click a source.</b></div></aside></section></div>`;
  }

  function showConflictMessages(){
    const c=selectedConflictObj(), plain=c?.plain_explanation||{}, all=plain.all_evidence||[];
    openSheet({title:'Which messages conflict?',subtitle:`${c?.name||'Selected conflict'} · exact governed evidence`,wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">PLAIN-ENGLISH CONFLICT EXPLANATION</span><h3>${esc(plain.headline||c?.root_cause||'')}</h3><p>${esc(plain.why_it_matters||'')}</p></div><div class="message-list-sheet">${all.map(x=>`<article class="sheet-message ${x.relation==='approved'?'approved':x.relation==='conflict'||x.relation==='informal'?'conflict':''}"><div><span class="chip ${x.relation==='approved'?'green':x.relation==='conflict'||x.relation==='informal'?'red':'cyan'}">${esc(cap(x.relation||'evidence'))}</span><b>${esc(x.source)} · ${esc(x.title)}</b><small>${esc(x.authority)} · ${esc(x.version||'current')}</small></div><blockquote>“${esc(x.message||'')}”</blockquote></article>`).join('')}</div><div class="sheet-section"><h4>Why JurisTwin keeps the approved source</h4><p>${esc(plain.why_canonical_wins||'')}</p></div>`});
  }

  function graphLayout(graph,reset=false){
    const key=state.selectedConflict;
    if(!state.graphPositions[key] || reset){
      const nodes=graph?.nodes||[], pos={}; const root=nodes.find(n=>n.type==='rule')||nodes[0];
      if(root) pos[root.id]={x:500,y:310};
      const rest=nodes.filter(n=>!root||n.id!==root.id); const rx=335,ry=225;
      rest.forEach((n,i)=>{ const a=(-Math.PI/2)+(i/Math.max(1,rest.length))*Math.PI*2; pos[n.id]={x:500+Math.cos(a)*rx,y:310+Math.sin(a)*ry}; });
      state.graphPositions[key]=pos;
    }
    return state.graphPositions[key];
  }

  function nodeTitle(n){
    const bySource={'Outlook Approval':'Product Owner Approval','Teams Message':'Operations Teams Message','FSD':'FSD v3 Requirement','Training Guide':'Training Guide','Customer Core System':'Customer Case','Gmail Connector':'Customer Complaint','QA Repository':'QA Test Rule'};
    return bySource[n.source]||n.label||n.id;
  }

  function nodeClass(n){ if(n.type==='rule') return 'root'; return n.relation||n.status||'default'; }

  function graphTitleLines(value,maxChars=31){
    const text=String(value||'').trim();
    if(text.length<=maxChars)return [text];
    const words=text.split(/\s+/),lines=[''];
    for(const word of words){
      const current=lines[lines.length-1];
      const next=current?`${current} ${word}`:word;
      if(next.length<=maxChars||lines.length===2){ lines[lines.length-1]=next; }
      else lines.push(word);
    }
    if(lines.length>2) lines.splice(1,lines.length-1,lines.slice(1).join(' '));
    if(lines[1]&&lines[1].length>maxChars+5)lines[1]=`${lines[1].slice(0,maxChars+2)}…`;
    return lines.slice(0,2);
  }

  function nodeDims(n){
    const title=String(nodeTitle(n));
    const meta=n?.source?`${n.source}${n.version?` · ${n.version}`:''}`:(n?.type==='rule'?'Canonical rule':'Evidence');
    const lines=graphTitleLines(title);
    const longest=Math.max(...lines.map(x=>x.length),Math.min(meta.length,34));
    // Give labels enough room instead of truncating important governed evidence names.
    const estimated=longest*(lines.length>1?9.0:9.35)+58;
    const w=clamp(Math.round(estimated),n?.type==='rule'?260:226,n?.type==='rule'?340:326);
    const h=lines.length>1?(n?.type==='rule'?96:92):(n?.type==='rule'?82:78);
    return {w,h,lines};
  }

  function graphNodeSvg(n,p){
    const {w,h,lines}=nodeDims(n);
    const title=String(nodeTitle(n));
    const meta=n.source?`${n.source}${n.version?` · ${n.version}`:''}`:(n.type==='rule'?'Canonical rule':'Evidence');
    const titleX=-w/2+28;
    const titleY=lines.length>1?-10:-4;
    const titleMarkup=lines.map((line,i)=>`<tspan x="${titleX}" dy="${i===0?0:21}">${esc(line)}</tspan>`).join('');
    const metaY=lines.length>1?34:24;
    const metaDisplay=meta.length>36?`${meta.slice(0,34)}…`:meta;
    return `<g class="graph-node ${esc(nodeClass(n))}" data-node-id="${esc(n.id)}" transform="translate(${p.x},${p.y})" tabindex="0" aria-label="${esc(title)}"><title>${esc(title)} — ${esc(meta)}</title><rect class="graph-node-bg" x="${-w/2}" y="${-h/2}" width="${w}" height="${h}" rx="13"/><circle class="graph-node-dot" cx="${-w/2+16}" cy="${-h/2+17}"/><text class="graph-node-title" x="${titleX}" y="${titleY}">${titleMarkup}</text><text class="graph-node-meta" x="${-w/2+16}" y="${metaY}">${esc(metaDisplay)}</text></g>`;
  }

  function drawGraph(reset=false){
    const svg=$('#graphSvg'); if(!svg||!state.graph)return;
    const graph=state.graph, pos=graphLayout(graph,reset), nodes=graph.nodes||[], edges=graph.edges||[];
    svg.innerHTML=`<defs><filter id="jtGlow" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#63daf0" flood-opacity=".24"/></filter></defs><g id="edgeLayer">${edges.map((e,i)=>{const a=pos[e.source]||{x:500,y:310},b=pos[e.target]||{x:500,y:310};return `<line id="edge-${i}" class="graph-edge ${esc(e.relation||'')}" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" data-source="${esc(e.source)}" data-target="${esc(e.target)}"/>`;}).join('')}</g><g id="nodeLayer">${nodes.map(n=>graphNodeSvg(n,pos[n.id]||{x:500,y:310})).join('')}</g>`;
    $$('.graph-node',svg).forEach(g=>{
      g.addEventListener('pointerdown',startGraphDrag);
      g.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){e.preventDefault();selectGraphNode(g.dataset.nodeId);} });
      g.classList.toggle('selected',g.dataset.nodeId===state.selectedNode);
    });
    renderInspector();
  }

  let graphDrag=null;
  function startGraphDrag(e){
    if(e.button!==0)return;
    e.preventDefault();
    const el=e.currentTarget, id=el.dataset.nodeId;
    graphDrag={el,id,pointerId:e.pointerId,startX:e.clientX,startY:e.clientY,moved:false};
    try{el.setPointerCapture(e.pointerId);}catch{}
    el.addEventListener('pointermove',moveGraphDrag);
    el.addEventListener('pointerup',endGraphDrag,{once:true});
    el.addEventListener('pointercancel',endGraphDrag,{once:true});
    selectGraphNode(id,true);
  }

  function graphPoint(e){
    const svg=$('#graphSvg'); if(!svg)return{x:500,y:310}; const pt=svg.createSVGPoint(); pt.x=e.clientX; pt.y=e.clientY; const ctm=svg.getScreenCTM(); return ctm?pt.matrixTransform(ctm.inverse()):{x:500,y:310};
  }

  function moveGraphDrag(e){
    if(!graphDrag||e.pointerId!==graphDrag.pointerId)return;
    const p=graphPoint(e), node=state.graph?.nodes?.find(n=>n.id===graphDrag.id), dims=nodeDims(node||{}), marginX=dims.w/2+14, marginY=dims.h/2+14;
    const pos=state.graphPositions[state.selectedConflict];
    pos[graphDrag.id]={x:clamp(p.x,marginX,1000-marginX),y:clamp(p.y,marginY,620-marginY)};
    if(Math.hypot(e.clientX-graphDrag.startX,e.clientY-graphDrag.startY)>3) graphDrag.moved=true;
    updateGraphGeometry();
  }

  function endGraphDrag(e){
    if(!graphDrag)return;
    const el=graphDrag.el;
    el.removeEventListener('pointermove',moveGraphDrag);
    try{el.releasePointerCapture(graphDrag.pointerId);}catch{}
    graphDrag=null;
  }

  function updateGraphGeometry(){
    const svg=$('#graphSvg'),pos=state.graphPositions[state.selectedConflict]; if(!svg||!pos)return;
    $$('.graph-node',svg).forEach(g=>{const p=pos[g.dataset.nodeId]; if(p)g.setAttribute('transform',`translate(${p.x},${p.y})`);});
    $$('.graph-edge',svg).forEach(line=>{const a=pos[line.dataset.source],b=pos[line.dataset.target];if(a){line.setAttribute('x1',a.x);line.setAttribute('y1',a.y);}if(b){line.setAttribute('x2',b.x);line.setAttribute('y2',b.y);}});
  }

  function selectGraphNode(id,rerender=true){
    state.selectedNode=id;
    if(rerender){ const svg=$('#graphSvg'); $$('.graph-node',svg).forEach(g=>g.classList.toggle('selected',g.dataset.nodeId===id)); }
    renderInspector();
  }

  function renderInspector(){
    const panel=$('#nodeInspector'); if(!panel||!state.graph)return;
    const n=state.graph.nodes.find(x=>x.id===state.selectedNode)||state.graph.nodes[0]; if(!n)return;
    const role=nodeClass(n)==='conflict'?'Conflicts':nodeClass(n)==='approved'?'Supports answer':n.type==='rule'?'Official rule':'Context';
    panel.innerHTML=`<span class="chip ${nodeClass(n)==='conflict'?'red':nodeClass(n)==='approved'?'green':'cyan'}" style="margin-top:12px">${esc(role)}</span><h3 class="inspector-title">${esc(nodeTitle(n))}</h3><dl class="inspector-kv compact-kv"><dt>Source</dt><dd>${esc(n.source||'Approved rule')}</dd><dt>Priority</dt><dd>${esc(n.authority||'System')}</dd><dt>Version</dt><dd>${esc(n.version||'Current')}</dd></dl>`;
  }

  function focusRoot(){
    const root=state.graph?.nodes?.find(n=>n.type==='rule'); if(!root)return; state.selectedNode=root.id; drawGraph(true); status('Graph re-centered on canonical rule','ok');
  }

  function renderTwin(){
    const sim=state.sim && state.sim.conflict_ref===state.selectedConflict ? state.sim : null;
    const c=selectedConflictObj();
    return `<div class="page"><section class="page-hero reveal"><div><div class="eyebrow">${esc(c?.name||'Selected issue')}</div><h2>Compare three fixes.</h2><p>Choose the best business outcome.</p></div><div class="hero-actions"><button class="btn" id="runTwin">${icon('play',12)} ${sim?'Compare again':'Compare outcomes'}</button>${sim?`<button class="btn primary" id="sendGovernance">Final approval ${icon('arrow',13)}</button>`:''}</div></section><div class="graph-tabs reveal" style="margin-bottom:14px">${state.conflicts.map(x=>`<button type="button" class="graph-tab ${x.conflict_ref===state.selectedConflict?'active':''}" data-twin-conflict="${esc(x.conflict_ref)}">${esc(x.name)}</button>`).join('')}</div>${sim?renderTwinResults(sim):renderTwinEmpty()}</div>`;
  }

  function renderTwinEmpty(){
    const c=selectedConflictObj();
    return `<section class="surface certificate-panel reveal manager-empty compact-empty"><div><div class="eyebrow">${esc(c?.name||'Selected issue')}</div><h3>Which fix works best?</h3><p>Compare delay, complaint risk and consistency.</p><button class="btn primary" id="runTwinEmpty">Compare options ${icon('play',12)}</button></div></section><section class="surface weights-panel reveal compact-weights"><h4>Business priorities</h4>${weightRows()}</section>`;
  }

  function weightRows(){
    const labels={delay:'Customer delay',complaint:'Complaint risk',alignment:'Process consistency'};
    return ['delay','complaint','alignment'].map(k=>`<div class="weight-row"><label>${labels[k]}</label><input type="range" min="10" max="70" value="${state.weights[k]}" data-weight="${k}"><b id="weight-${k}">${state.weights[k]}%</b></div>`).join('');
  }

  function renderTwinResults(sim){
    const cert=sim.analysis?.decision_certificate||{}, actions=sim.analysis?.recommended_actions||[], plain=sim.analysis?.plain_language||{}, outcome=plain.customer_outcome||{};
    return `<div class="twin-summary reveal"><span class="chip green">RECOMMENDATION READY</span><span><strong>${fmt(sim.analysis?.scenario_count||1500)}</strong> scenarios checked</span></div><section class="decision-lanes reveal">${sim.options.map(o=>`<article class="decision-lane ${state.selectedOption===o.key?'selected':''} ${sim.recommended_option===o.key?'recommended':''}" data-option="${esc(o.key)}" tabindex="0"><div class="lane-key">Option ${esc(o.key)}</div><h3>${esc(sim.analysis?.scenario_profile==='income_document_rule'?(PITCH_OPTION_LABELS[o.key]||cap(o.name)):cap(o.name))}</h3><div class="fit-score">${Number(o.decision_fit).toFixed(1)}<small>/100</small></div><div class="fit-bar"><i style="width:${clamp(Number(o.decision_fit),0,100)}%"></i></div><div class="lane-metrics"><div><b>${Number(o.predicted_delay_days).toFixed(1)}d</b><span>delay</span></div><div><b>${riskLabel(o.complaint_probability)}</b><span>complaints</span></div><div><b>${pct(o.policy_alignment)}</b><span>consistency</span></div></div>${o.key==='B'?`<div class="lane-gap">${fmt(o.applications_affected)} cases still exposed</div>`:''}${o.key===sim.recommended_option?`<div class="process-opt-label">RECOMMENDED</div><div class="action-chips">${actions.slice(0,3).map(a=>`<span>${esc(brief(a,44))}</span>`).join('')}</div>`:''}</article>`).join('')}</section><section class="surface recommendation-plain reveal compact-recommendation"><div class="recommendation-head"><div><span class="eyebrow">BEST CHOICE · OPTION ${esc(sim.recommended_option||'C')}</span><h3>${esc(brief(plain.headline||sim.analysis?.recommended_title||'Choose the complete response.',95))}</h3></div><span class="chip green">BEST OUTCOME</span></div><div class="outcome-strip"><div><small>DELAY</small><b>${Number(outcome.delay_before_days??0).toFixed(1)}d <i>→</i> ${Number(outcome.delay_after_days??0).toFixed(1)}d</b></div><div><small>COMPLAINTS</small><b>${fmt(outcome.complaint_before_pct)}% <i>→</i> ${fmt(outcome.complaint_after_pct)}%</b></div><div><small>EXPOSED</small><b>${fmt(outcome.affected_before)} <i>→</i> ${fmt(outcome.affected_after)}</b></div><div><small>CONSISTENCY</small><b>${fmt(outcome.alignment_before_pct)}% <i>→</i> ${fmt(outcome.alignment_after_pct)}%</b></div></div><div class="recommendation-actions"><span><b>${esc(brief(plain.non_technical_takeaway||plain.why_recommended||plain.headline||'Complete alignment wins.',110))}</b></span><div><details class="inline-details"><summary>Why not A/B?</summary><p><b>A:</b> ${esc(brief(plain.why_not_a||'Leaves the issue in place.',75))}<br><b>B:</b> ${esc(brief(plain.why_not_b||'Only fixes part of the problem.',75))}</p></details><button class="btn quiet" id="twinTechnicalProof">Technical proof</button></div></div></section><section class="twin-bottom"><aside class="surface weights-panel reveal compact-weights"><h4>Business priorities</h4>${weightRows()}</aside></section>`;
  }

  function showTwinTechnicalProof(){
    const sim=state.sim;if(!sim)return;const cert=sim.analysis?.decision_certificate||{};
    openSheet({title:'Why the simulator trusts this recommendation',subtitle:'Technical proof beneath the plain-English answer',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">WHITE-BOX FUTURE SIMULATOR</span><h3>Option ${esc(sim.recommended_option)} remains the best choice when assumptions move.</h3><p>${esc(sim.analysis?.recommended_rationale||'')}</p></div><div class="metric-strip model-card-metrics"><div class="metric"><div class="metric-label">SCENARIOS</div><div class="metric-value">${fmt(sim.analysis?.scenario_count||1500)}</div><div class="metric-note">Monte Carlo stress cases</div></div><div class="metric good"><div class="metric-label">SENSITIVITY STABILITY</div><div class="metric-value">${pct(cert.sensitivity_stability_pct||sim.analysis?.robustness_score)}</div><div class="metric-note">±10pp priority tests</div></div><div class="metric good"><div class="metric-label">P10 FIT</div><div class="metric-value">${Number(cert.worst_case_fit_p10||0).toFixed(1)}</div><div class="metric-note">conservative fit floor</div></div><div class="metric"><div class="metric-label">PARETO</div><div class="metric-value">${cert.pareto_optimal?'YES':'NO'}</div><div class="metric-note">non-dominated option</div></div></div><div class="sheet-section"><h4>Model boundary</h4><p>${esc(sim.analysis?.validation_note||'')}</p></div>`});
  }

  async function runTwin(){
    try {
      const c=selectedConflictObj(); if(!c)throw new Error('Select a conflict first');
      status('Running 1,500-scenario stress test…');
      const sum=state.weights.delay+state.weights.complaint+state.weights.alignment;
      const weights={delay:state.weights.delay/sum,complaint:state.weights.complaint/sum,alignment:state.weights.alignment/sum};
      state.sim=await api(`/simulations/conflict/${encodeURIComponent(c.conflict_ref)}/run`,{method:'POST',body:JSON.stringify({weights})}); state.selectedOption=state.sim.recommended_option||'C'; renderShell(); status(`${c.name} · decision certificate issued`,'ok');
    } catch(e){ status(e.message,'error',3200); }
  }

  async function openGovernance(){
    if(!state.sim)return;
    try {
      const conflictRef=state.sim.conflict_ref||state.selectedConflict;
      const gate=await api(`/assurance/governance-gate/${encodeURIComponent(conflictRef)}`); const option=state.sim.options.find(o=>o.key===state.selectedOption)||state.sim.options[0];
      const labelMap={'Canonical authority':'Official owner','Impact is explainable':'Affected cases','Decision robustness':'Stable recommendation','Ledger integrity':'Audit trail','No unresolved critical security block':'Security'};
      const passed=(gate.checks||[]).filter(x=>x.ok).length,total=(gate.checks||[]).length,blocked=(gate.checks||[]).filter(x=>!x.ok);
      openSheet({title:'Final approval',subtitle:`${passed}/${total} checks passed`,body:`<div class="sheet-section manager-gate compact-gate"><div class="gate-status-line"><span class="chip ${gate.status==='PASS'?'green':'red'}">${gate.status==='PASS'?'READY':'REVIEW'}</span><span class="gate-count">${passed}/${total}</span></div><h4>Publish Option ${esc(state.selectedOption)}?</h4>${blocked.length?`<div class="gate-block-message">${icon('lock',15)}<div><b>Approval locked</b><span>Fix ${blocked.length} check${blocked.length===1?'':'s'} first.</span></div></div>`:`<div class="gate-ready-message">${icon('check',15)}<div><b>Ready to publish</b></div></div>`}</div><div class="sheet-section"><div class="sheet-list manager-check-list compact-check-list">${(gate.checks||[]).map(c=>`<div class="sheet-row ${c.ok?'':'blocked'}" title="${esc(c.detail||'')}"><i>${c.ok?'✓':'!'}</i><div><b>${esc(labelMap[c.label]||c.label)}</b></div><span>${c.ok?'READY':'FIX'}</span></div>`).join('')}</div></div><details class="technical-details"><summary>Technical gate</summary><p>Backend score: ${gate.score}/100.</p></details>`,footer:`<button class="btn" data-close-sheet type="button">Cancel</button><button class="btn primary" id="confirmPublish" type="button" ${gate.status!=='PASS'||state.selectedOption!=='C'?'disabled title="Complete every required check first"':''}>Approve & publish</button>`,onOpen:()=>$('#confirmPublish')?.addEventListener('click',publishDecision)});
    } catch(e){ status(e.message,'error',3200); }
  }

  async function publishDecision(){
    const btn=$('#confirmPublish'); if(btn){btn.disabled=true;btn.textContent='Publishing…';}
    try {
      const approval=await api(`/approvals/simulation/${state.sim.sim_ref}/submit`,{method:'POST',body:JSON.stringify({selected_option:'C',comments:'Finals governed resolution'})});
      const result=await api(`/approvals/${approval.approval_ref}/approve`,{method:'POST',body:JSON.stringify({comments:'Approved after JurisTwin assurance gate'})});
      if(result.decision_contract?.decision_ref)state.decisionRefs[state.sim.conflict_ref]=result.decision_contract.decision_ref; state.assurance=null;state.readiness=null; closeSheet(); await refreshCore(); state.page='overview'; renderShell(); status(`Decision ${result.decision_contract?.decision_ref||'published'} · ${result.propagation?.cases||0} cases protected`,'ok',3600);
    } catch(e){ status(e.message,'error',3400); if(btn){btn.disabled=false;btn.textContent='Approve & publish';} }
  }

  function renderAssurance(){
    const a=state.assurance,r=state.readiness;
    if(!a||!r)return `<div class="page compact-page"><section class="page-hero reveal"><div><h2>Safe to publish?</h2></div><div class="hero-actions"><button class="btn primary" id="loadAssurance">Check now ${icon('shield',13)}</button></div></section><section class="surface certificate-panel reveal manager-empty compact-empty"><div><div class="eyebrow">FINAL CHECK</div><h3>One screen before approval.</h3><p>Access, impact and audit are checked together.</p></div></section></div>`;
    const gate=a.flagship_governance_gate||{},tel=a.telemetry||{},inv=a.invariants||{};
    const gateChecks=gate.checks||[], gatePassed=gateChecks.filter(x=>x.ok).length;
    const ready=r.status==='READY'&&gate.status==='PASS';
    return `<div class="page compact-page"><section class="page-hero reveal"><div><h2>${ready?'Ready to publish.':'Review before publishing.'}</h2></div><div class="hero-actions"><button class="btn" id="decisionReplay">History</button><button class="btn" id="proofPack">Audit proof</button><button class="btn danger" id="attackSentinel">Security test</button><button class="btn square" id="refreshAssurance" title="Refresh">${icon('reset',14)}</button></div></section><section class="surface assurance-hero reveal manager-assurance compact-assurance"><div class="assurance-score"><strong>${r.score}</strong><small>/100</small></div><div class="assurance-copy"><span class="chip ${ready?'green':'amber'}">${ready?'CLEAR':'REVIEW'}</span><h3>${gatePassed}/${gateChecks.length} checks passed</h3><div class="manager-assurance-badges"><span>${icon('lock',12)} Access</span><span>${icon('shield',12)} Audit</span><span>${icon('spark',12)} Live</span></div><div class="assurance-actions"><button class="btn" id="proofPackInline">Audit proof</button><button class="btn" id="rolloutInline">Rollout</button><button class="btn danger" id="attackInline">Test</button></div></div></section><section class="control-columns compact-control-columns"><div class="surface control-panel reveal"><div class="control-head"><div><b>Approval</b></div><span>${gatePassed}/${gateChecks.length}</span></div>${gateChecks.map(c=>controlRow(({'Canonical authority':'Official owner confirmed','Impact is explainable':'Affected cases accounted for','Decision robustness':'Recommendation stable','Ledger integrity':'Audit trail intact','No unresolved critical security block':'No critical alerts'})[c.label]||c.label,c.detail,c.ok?'READY':'FIX',c.ok)).join('')}</div><div class="surface control-panel reveal"><div class="control-head"><div><b>System safety</b></div><span>${esc(inv.status||'')}</span></div>${(inv.checks||[]).map(c=>controlRow(cap(c.key),c.detail,c.ok?'OK':'CHECK',c.ok)).join('')}</div></section><details class="technical-details page-technical reveal"><summary>Technical performance</summary><p>Success ${Number(tel.success_rate_pct||0).toFixed(0)}% · p95 ${Number(tel.latency_ms?.p95||0).toFixed(1)} ms · gate ${gate.score||0}/100.</p><button class="btn quiet" id="rolloutPlan">Rollout details</button></details></div>`;
  }

  function controlRow(label,detail,stateText,ok=true){ return `<div class="control-row compact-control-row" title="${esc(detail||'')}"><i class="control-icon">${ok?'✓':'!'}</i><div><b>${esc(label)}</b></div><span class="control-state">${esc(stateText)}</span></div>`; }

  async function loadAssurance(){
    try { status('Running assurance controls…'); const [readiness,assurance]=await Promise.all([api('/system/readiness'),api('/assurance/overview')]); state.readiness=readiness;state.assurance=assurance;renderShell();status('Assurance verified','ok'); } catch(e){ status(e.message,'error',3200); }
  }

  async function showProofPack(){
    const c=selectedConflictObj(); if(!c){status('Select an issue first','error');return;}
    openSheet({title:'Audit proof for this decision',subtitle:`${c.name} · who approved it, what it affected, and whether the record is intact`,body:`<div class="sheet-section"><p>Building the audit record from the current decision and evidence…</p></div>`});
    try {
      const detail=await decisionForConflict(c); const ref=detail?.decision?.decision_ref||'';
      const qs=new URLSearchParams({conflict_ref:c.conflict_ref}); if(ref)qs.set('decision_ref',ref);
      const d=await api(`/assurance/proof-pack?${qs.toString()}`); const proof=d.proof||{}, ledger=d.ledger||{}, impact=d.impact||{}, ai=d.ai_assurance||{};
      $('.sheet-body',portal).innerHTML=`<div class="sheet-section manager-proof-pack"><span class="chip ${d.status==='ASSURED'?'green':'amber'}">${d.status==='ASSURED'?'RECORD PROTECTED':'CHECK RECORD'}</span><h4>Everything needed to explain this decision later.</h4><p>This record links the decision to its source, affected cases, approval history and tamper check.</p></div><div class="manager-proof-pack-grid"><article><small>DECISION</small><b>${esc(d.subject?.decision_ref||d.subject?.conflict_ref||c.conflict_ref)}</b><span>${esc(c.name)}</span></article><article><small>CUSTOMER IMPACT</small><b>${fmt(impact.affected_cases||0)} cases</b><span>accounted for in the impact trail</span></article><article><small>AUDIT HISTORY</small><b>${fmt(ledger.entries||0)} recorded events</b><span>${ledger.verified?'History verified':'History needs review'}</span></article><article><small>AI AUTHORITY</small><b>${ai.model_can_publish===false?'Cannot publish':'Review required'}</b><span>Only an authorised human can make the decision official</span></article></div><div class="proof-verify manager-proof-verify" id="proofVerifyState"><span class="chip cyan">READY TO CHECK</span><p>Verify that this audit record has not been changed since it was created.</p></div><div class="feature-actions"><button class="btn primary" id="verifyThisProof">Verify record</button></div><details class="technical-details"><summary>Technical fingerprint</summary><dl class="sheet-kv"><dt>Digest</dt><dd class="mono">${esc(shortHash(proof.bundle_digest))}</dd><dt>Signature</dt><dd class="mono">${esc(shortHash(proof.signature))}</dd><dt>Algorithm</dt><dd>${esc(proof.signature_algorithm||'HMAC-SHA256')}</dd><dt>Key</dt><dd>${esc(proof.key_id||'juristwin-assurance')}</dd></dl></details><!-- Verify this proof -->`;
      $('#verifyThisProof')?.addEventListener('click',async()=>{const b=$('#verifyThisProof');if(b){b.disabled=true;b.textContent='Checking…';}try{const v=await api('/assurance/verify-proof',{method:'POST',body:JSON.stringify({bundle_digest:proof.bundle_digest,signature:proof.signature})});const box=$('#proofVerifyState');if(box)box.innerHTML=`<span class="chip ${v.valid?'green':'red'}">${v.valid?'RECORD VERIFIED':'RECORD CHANGED'}</span><p>${v.valid?'The backend independently confirmed that this audit record is authentic and unchanged.':'The record did not pass verification and should not be relied on.'}</p>`;status(v.valid?'Audit record verified':'Audit verification failed',v.valid?'ok':'error',3000);}catch(e){status(e.message,'error',3000);}finally{if(b){b.disabled=false;b.textContent='Check again';}}});
    } catch(e){ $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><p style="color:var(--red)">${esc(e.message)}</p></div>`; }
  }

  async function attackSentinel(){
    openSheet({title:'Attack Sentinel',subtitle:'Live adversarial self-test',body:`<div class="sheet-section"><p>Testing tamper resistance, authorization, input containment and business-state invariants…</p></div>`});
    try {
      const d=await api('/live/red-team',{method:'POST',body:'{}'});
      $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><span class="chip green">${esc(d.status)}</span><div class="sheet-score" style="margin-top:10px">${d.score}<small>/100</small></div><p>${d.passed}/${d.total} controls passed · ${d.state_mutations_persisted} persisted attack mutations · ${d.canonical_decisions_modified} canonical decisions modified.</p></div><div class="sheet-section"><div class="sheet-list">${d.tests.map(t=>`<div class="sheet-row"><i>✓</i><div><b>${esc(t.label)}</b><small>${esc(t.proof)}</small></div><span>PASS</span></div>`).join('')}</div></div>`;
    } catch(e){ $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><p style="color:var(--red)">${esc(e.message)}</p></div>`; }
  }

  function ago(isoValue){
    if(!isoValue)return 'Never synced';
    const d=new Date(isoValue); if(Number.isNaN(d.getTime()))return isoValue;
    const sec=Math.max(0,Math.round((Date.now()-d.getTime())/1000));
    if(sec<60)return `${sec}s ago`;
    if(sec<3600)return `${Math.floor(sec/60)}m ago`;
    if(sec<86400)return `${Math.floor(sec/3600)}h ago`;
    return `${Math.floor(sec/86400)}d ago`;
  }

  function auditActionLabel(v=''){
    const map={
      POLICY_QUERY_ANSWERED:'Policy question answered',MEMORY_SEARCH_EXECUTED:'Evidence search',SOURCE_SCOPE_UPDATED:'Source scope changed',
      CUSTOMER_EXPORT_AUTHORIZED:'Customer export authorised',CUSTOMER_EXPORT_BLOCKED:'Customer export blocked',DLP_DOWNLOAD_BLOCKED:'Evidence download blocked',
      EVIDENCE_DOWNLOAD_AUTHORIZED:'Evidence download authorised',EVIDENCE_INGESTED:'Evidence ingested',CONFLICT_DETECTED:'Conflict detected',
      SECURITY_SHIELD_UPDATED:'Security control changed',RBAC_POLICY_UPDATED:'Role policy changed',INTEGRATION_PAUSED:'Connector paused',INTEGRATION_CONNECTED:'Connector connected'
    };
    return map[v]||cap(v);
  }

  function sourcePolicyBadge(x){
    if(!x.retrieval_enabled || x.status==='inactive')return '<span class="chip red">OFF</span>';
    if(x.policy_authority_enabled)return '<span class="chip green">OFFICIAL SOURCE</span>';
    return '<span class="chip cyan">REFERENCE ONLY</span>';
  }


  function sourceScopeSummary(x){
    if(x.key==='teams')return `Groups: ${(x.allowed_channels||[]).join(', ')||'No approved groups configured'} · Personal DMs blocked`;
    if(['outlook','gmail'].includes(x.key))return `Official senders: ${(x.allowed_sender_roles||[]).join(', ')||'No sender roles configured'} · Casual mail blocked`;
    if(x.key==='sharepoint')return `Libraries: ${(x.allowed_libraries||[]).join(', ')||'Approved libraries only'}`;
    if(x.key==='customer_core')return 'Customer impact only · cannot set company policy';
    if(x.key==='webhook')return 'Signed live events · quarantined until governance';
    return x.scope_label||'Configured source scope';
  }

  function renderGovernance(){
    const d=state.security;
    if(!d)return `<div class="page compact-page"><section class="page-hero reveal"><div><span class="eyebrow">PRIVACY & SECURITY</span><h2>What can JurisTwin use?</h2></div><div class="hero-actions"><button class="btn primary" id="refreshGovernance">Load controls</button></div></section><section class="surface certificate-panel reveal manager-empty compact-empty"><div><div class="empty-icon">${icon('lock',22)}</div><h3>Private by default.</h3><p>Only approved work sources are used.</p></div></section></div>`;
    const sources=d.source_policies||[], roles=d.role_matrix||[], audit=d.audit||[], transfer=d.transfer_security||{}, realtime=d.realtime||{};
    const teams=sources.find(x=>x.key==='teams'), outlook=sources.find(x=>x.key==='outlook');
    const currentRole=(roles||[]).find(r=>String(r.role||r.name||r.display_name||'').toLowerCase()===String(state.user?.role||'manager').toLowerCase()) || roles.find(r=>String(r.display_name||'').toLowerCase().includes(String(state.user?.role||'manager').toLowerCase()));
    const visibleKeys=['teams','outlook','gmail','sharepoint','customer_core','qa'];
    const visibleSources=sources.filter(x=>visibleKeys.includes(x.key));
    const moreSources=sources.filter(x=>!visibleKeys.includes(x.key)&&['onedrive','clickup','webhook'].includes(x.key));
    return `<div class="page governance-page compact-page"><section class="page-hero reveal"><div><span class="eyebrow">PRIVACY & SECURITY</span><h2>Protected by default.</h2></div><div class="hero-actions"><span class="chip green">${icon('shield',11)} PROTECTED</span><button class="btn" id="openControlCoverage">Changes</button><button class="btn primary" id="refreshGovernance">Refresh</button></div></section><section class="manager-security-grid governance-summary reveal compact-security-grid"><article><div class="security-icon safe">${icon('lock',19)}</div><small>TEAMS DMs</small><b>${teams?.personal_dm_allowed?'REVIEW':'BLOCKED'}</b></article><article><div class="security-icon safe">${icon('check',19)}</div><small>CASUAL EMAIL</small><b>${outlook?.official_only?'BLOCKED':'REVIEW'}</b></article><article><div class="security-icon safe">${icon('shield',19)}</div><small>CLIENT AI TRAINING</small><b>OFF</b></article><article><div class="security-icon live">${icon('spark',19)}</div><small>LIVE REFRESH</small><b>ON</b></article></section><section class="surface source-governance-panel reveal"><div class="section-head compact"><div><span class="eyebrow">1 · SOURCES</span><h3>Where JurisTwin may look</h3></div><span class="chip green">PRIVATE CONTENT BLOCKED</span></div><div class="source-policy-grid manager-source-grid compact-source-grid">${visibleSources.map(x=>`<article class="source-policy-card manager-source-card compact-source-card"><div class="source-policy-top"><div><b>${esc(x.name)}</b><small>${esc(brief(x.scope_label||x.kind,42))}</small></div>${sourcePolicyBadge(x)}</div><div class="manager-source-state compact-source-state"><span class="${x.retrieval_enabled?'allow':'deny'}">${x.retrieval_enabled?'✓ Used':'× Off'}</span><span class="${x.policy_authority_enabled?'allow':'neutral'}">${x.policy_authority_enabled?'✓ Official':'Reference'}</span><span class="deny">AI training: off</span></div><footer><span><b class="freshness-dot ${String(x.freshness_state||'').toLowerCase()}"></b>${esc(x.freshness_state||'CHECK')} · ${ago(x.last_sync_at)}</span><button class="btn quiet" data-source-config="${esc(x.key)}">Access</button></footer></article>`).join('')}</div>${moreSources.length?`<details class="technical-details compact-details"><summary>More connected sources</summary><div class="compact-tags">${moreSources.map(x=>`<span>${esc(x.name)} · ${x.retrieval_enabled?'Used':'Off'}</span>`).join('')}</div></details>`:''}<div class="privacy-rule-strip manager-privacy-strip compact-privacy-strip"><div>${icon('lock',16)}<span>Teams groups only</span></div><div>${icon('shield',16)}<span>Official email only</span></div><div>${icon('spark',16)}<span>No client-data training</span></div></div></section><section class="security-two-col reveal"><article class="surface security-card"><div class="section-head compact"><div><span class="eyebrow">2 · CUSTOMER DATA</span><h3>Who can export?</h3></div><span class="chip green">ROLE-BASED</span></div>${currentRole?`<div class="current-access-card compact-current-access"><div>${icon('shield',16)}<span><small>YOUR ACCESS</small><b>${esc(currentRole.display_name||cap(state.user?.role||'manager'))}</b></span></div><div class="access-verdicts"><span class="${currentRole.masked_customer_export?'allow':'deny'}">Masked: ${currentRole.masked_customer_export?'Allowed':'Blocked'}</span><span class="${currentRole.full_customer_export?'allow':'deny'}">Full: ${currentRole.full_customer_export?'Allowed':'Blocked'}</span></div></div>`:''}<div class="access-matrix compact-access-matrix"><div class="access-row header"><b>Role</b><b>View</b><b>Masked</b><b>Full</b></div>${roles.map(r=>`<div class="access-row"><b>${esc(r.display_name)}</b><span>${esc(cap(r.view_customer_data))}</span><span class="${r.masked_customer_export?'allow':'deny'}">${r.masked_customer_export?'Yes':'No'}</span><span class="${r.full_customer_export?'allow':'deny'}">${r.full_customer_export?'Yes':'No'}</span></div>`).join('')}</div><div class="export-demo compact-export-demo"><input class="form-control" id="exportReason" value="Lecturer demo · controlled customer-data export" aria-label="Export reason"><div><button class="btn" id="maskedExport">Masked export</button><button class="btn danger" id="fullExport">Try full export</button></div><small>Every attempt is logged.</small></div></article><article class="surface security-card"><div class="section-head compact"><div><span class="eyebrow">3 · DATA TRANSFER</span><h3>Protected end to end</h3></div><span class="chip green">SECURE</span></div><div class="data-flow manager-data-flow compact-data-flow"><span>Work apps</span><i>→</i><span>Secure link</span><i>→</i><span>Privacy</span><i>→</i><span>Access</span><i>→</i><span>JurisTwin</span></div><div class="simple-security-list compact-security-list"><div>${icon('shield',14)}<span><b>Transit encrypted</b></span></div><div>${icon('lock',14)}<span><b>API keys server-side</b></span></div><div>${icon('check',14)}<span><b>Stored data encrypted</b></span></div><div>${icon('spark',14)}<span><b>Live updates signed</b></span></div></div><details class="technical-details"><summary>Technical details</summary><dl class="security-kv"><dt>Transport</dt><dd>${esc(transfer.production_transport||'TLS 1.2+ / 1.3')}</dd><dt>Ingress</dt><dd>${esc(transfer.signed_ingress||'HMAC-SHA256')}</dd><dt>Keys</dt><dd>${esc(transfer.api_keys||'Server environment')}</dd><dt>Storage</dt><dd>${esc(transfer.at_rest||'Encrypted in production')}</dd></dl></details></article></section><section class="surface realtime-panel reveal compact-realtime"><div class="section-head compact"><div><span class="eyebrow">4 · LIVE</span><h3>Latest approved information</h3></div><span class="runtime large"><i></i><span>LIVE</span></span></div><div class="live-source-monitor"><div><small>OUTLOOK</small><b>${esc(sources.find(x=>x.key==='outlook')?.freshness_state||'CHECK')}</b><span>${ago(sources.find(x=>x.key==='outlook')?.last_sync_at)}</span></div><div><small>TEAMS</small><b>${esc(sources.find(x=>x.key==='teams')?.freshness_state||'CHECK')}</b><span>${ago(sources.find(x=>x.key==='teams')?.last_sync_at)}</span></div><div><small>CUSTOMER CORE</small><b>${esc(sources.find(x=>x.key==='customer_core')?.freshness_state||'LIVE')}</b><span>${ago(sources.find(x=>x.key==='customer_core')?.last_sync_at)}</span></div><div><small>ANSWERS</small><b>LIVE</b><span>Rechecked per question</span></div></div><div class="feature-actions"><button class="btn" id="governanceAskLatest">Ask now</button><button class="btn primary" id="governanceLiveTest">Test update</button></div></section><section class="surface audit-panel reveal compact-audit"><div class="section-head compact"><div><span class="eyebrow">5 · AUDIT</span><h3>Who did what?</h3></div><span class="chip cyan">ON</span></div><div class="audit-table manager-audit"><div class="audit-row header"><b>Time</b><b>Person</b><b>Action</b><b>Outcome</b></div>${audit.slice(0,8).map(x=>`<div class="audit-row"><span>${esc(ago(x.created_at))}</span><b>${esc(x.actor||'system')}</b><span>${esc(auditActionLabel(x.action))}</span><div><span>${esc(brief(String(x.subject||''),58))}</span><small>${esc(x.result||'Recorded')}</small></div></div>`).join('')||'<div class="feature-empty">No activity yet.</div>'}</div><details class="technical-details"><summary>Audit integrity</summary><p>Important actions are linked into the decision ledger for later verification.</p></details></section></div>`;
  }

  async function loadSecurity(showStatus=true){
    try{
      if(showStatus)status('Refreshing privacy, source and audit controls…');
      state.security=await api('/system/security-overview');
      if(state.page==='governance')renderShell();
      if(showStatus)status('Data governance refreshed','ok');
    }catch(e){status(e.message,'error',3200);}
  }

  function startSecurityPulse(){
    if(state.securityTimer)return;
    state.securityTimer=setInterval(async()=>{
      if(state.page!=='governance')return stopSecurityPulse();
      try{state.security=await api('/system/security-overview'); if(state.page==='governance')renderShell();}catch{}
    },15000);
  }
  function stopSecurityPulse(){if(state.securityTimer){clearInterval(state.securityTimer);state.securityTimer=null;}}

  async function showSourceConfig(key){
    if(!state.security)await loadSecurity(false);
    const x=(state.security?.source_policies||[]).find(v=>v.key===key); if(!x)return;
    const isTeams=key==='teams', isMail=['outlook','gmail'].includes(key), isDocs=key==='sharepoint';
    const immutablePrivacy=isTeams?'Personal and 1-to-1 DMs stay blocked.':(isMail?'Only approved official mail may influence policy.':'Client content never trains the AI.');
    let scopeEditor='';
    if(isTeams) scopeEditor=`<label class="manager-scope-editor"><span>APPROVED GROUPS / CHANNELS</span><input class="form-control" id="sourceScopeList" value="${esc((x.allowed_channels||[]).join(', '))}" placeholder="Operations Policy, Compliance"></label>`;
    else if(isMail) scopeEditor=`<label class="manager-scope-editor"><span>APPROVED SENDER ROLES</span><input class="form-control" id="sourceScopeList" value="${esc((x.allowed_sender_roles||[]).join(', '))}" placeholder="Product Owner, Compliance Manager"></label>`;
    else if(isDocs) scopeEditor=`<label class="manager-scope-editor"><span>APPROVED LIBRARIES</span><input class="form-control" id="sourceScopeList" value="${esc((x.allowed_libraries||[]).join(', '))}" placeholder="Approved Policies, Controlled SOPs"></label>`;
    const authorityLocked=isTeams || ['customer_core','qa','onedrive','clickup','webhook','vector'].includes(key);
    openSheet({title:`${x.name} access`,subtitle:'Choose what JurisTwin may use',wide:true,body:`<div class="source-config-simple enhanced compact-source-config"><div><span>${icon('check',14)}</span><p><b>Use for answers</b></p><span class="chip ${x.retrieval_enabled?'green':'red'}">${x.retrieval_enabled?'ON':'OFF'}</span></div><div><span>${icon('shield',14)}</span><p><b>Official source</b></p><span class="chip ${!authorityLocked&&x.policy_authority_enabled?'green':'cyan'}">${!authorityLocked&&x.policy_authority_enabled?'YES':'NO'}</span></div><div><span>${icon('lock',14)}</span><p><b>${esc(immutablePrivacy)}</b></p><span class="chip green">LOCKED</span></div><div><span>${icon('spark',14)}</span><p><b>AI training</b></p><span class="chip green">OFF</span></div></div>${scopeEditor}<div class="source-rule-callout compact-callout"><b>Conflict rule</b><p>Highest approved authority wins. Majority is only used at the same authority level.</p></div><div class="feature-actions"><button class="btn ${x.retrieval_enabled?'danger':'primary'}" id="toggleRetrieval">${x.retrieval_enabled?'Turn off':'Use for answers'}</button>${!authorityLocked?`<button class="btn" id="toggleAuthority">${x.policy_authority_enabled?'Make reference-only':'Allow as official'}</button>`:''}${scopeEditor?`<button class="btn primary" id="saveSourceScope">Save scope</button>`:''}</div><details class="technical-details"><summary>Technical details</summary><p>Status ${esc(x.status)} · freshness ${esc(x.freshness_state||'—')} · client training off.</p></details>`,onOpen:()=>{ $('#toggleRetrieval')?.addEventListener('click',()=>updateSourcePolicy(key,{retrieval_enabled:!x.retrieval_enabled})); $('#toggleAuthority')?.addEventListener('click',()=>updateSourcePolicy(key,{policy_authority_enabled:!x.policy_authority_enabled})); $('#saveSourceScope')?.addEventListener('click',()=>{ const values=($('#sourceScopeList')?.value||'').split(',').map(v=>v.trim()).filter(Boolean).slice(0,12); const config=isTeams?{allowed_channels:values}:isMail?{allowed_sender_roles:values}:isDocs?{allowed_libraries:values}:{}; updateSourcePolicy(key,config); }); }});
  }

  async function updateSourcePolicy(key,config){
    try{
      const r=await api(`/integrations/${encodeURIComponent(key)}/policy`,{method:'PATCH',body:JSON.stringify({config})});
      closeSheet(); state.security=null; state.overviewAnswer=null; await loadSecurity(false); renderShell();
      status(`${r.name} source scope updated`,'ok',3000);
    }catch(e){status(e.message,'error',3200);}
  }

  async function showAnswerSourcePolicy(){
    const r=state.overviewAnswer; if(!r)return;
    if(!state.security){try{state.security=await api('/system/security-overview');}catch{}}
    const res=r.resolution||{}, excluded=res.excluded||[];
    const sources=(state.security?.source_policies||[]).filter(x=>x.retrieval_enabled&&x.status!=='inactive').slice(0,6);
    openSheet({title:'Source rules',subtitle:'Why this answer is trusted',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">3 SIMPLE RULES</span><h3>Approved scope → official source → same-tier majority only if needed</h3></div><div class="manager-resolution-steps compact-resolution-steps"><article><span>1</span><div><b>Approved sources only</b></div></article><article><span>2</span><div><b>Private/casual content blocked</b></div></article><article><span>3</span><div><b>Highest authority wins</b></div></article></div><div class="sheet-section"><h4>Currently allowed</h4><div class="compact-tags">${sources.map(x=>`<span>${esc(x.name)}</span>`).join('')}</div></div><div class="sheet-section"><h4>Left out of this answer</h4>${excluded.length?`<div class="sheet-list">${excluded.slice(0,6).map(x=>`<div class="sheet-row"><i>×</i><div><b>${esc(x.title||x.source)}</b><small>${esc(brief(x.reason||'Excluded by source rules',72))}</small></div><span>NOT USED</span></div>`).join('')}</div>`:'<p>None.</p>'}<div class="feature-actions"><button class="btn primary" id="openDataGovFromPolicy">Privacy & Security</button></div></div><details class="technical-details"><summary>Technical retrieval</summary><p>Keyword + semantic matching runs only inside the approved source boundary. Relevance never overrides authority.</p></details>`,onOpen:()=>$('#openDataGovFromPolicy')?.addEventListener('click',()=>{closeSheet();navigate('governance');})});
  }

  async function runCustomerExport(mode){
    const reason=($('#exportReason')?.value||'').trim();
    if(reason.length<8){status('Give an audit reason for the export','error');return;}
    try{
      const headers={'Content-Type':'application/json'}; if(state.token)headers.Authorization=`Bearer ${state.token}`;
      const response=await fetch('/api/cases/export.csv',{method:'POST',headers,body:JSON.stringify({mode,reason})});
      if(!response.ok){const d=await response.json().catch(()=>({}));throw new Error(d.detail||`Export blocked (${response.status})`);}
      const blob=await response.blob(); const url=URL.createObjectURL(blob); const a=document.createElement('a');a.href=url;a.download=`juristwin_customer_export_${mode}.csv`;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);
      state.security=null; await loadSecurity(false); status(`${cap(mode)} customer export authorised and audited`,'ok',3200);
    }catch(e){state.security=null;await loadSecurity(false);status(e.message,'error',3600);}
  }

  function renderEvidence(){
    const d=state.lastChallenge;
    return `<div class="page compact-page"><section class="page-hero reveal"><div><h2>Test a new message.</h2></div></section><section class="evidence-workspace"><article class="surface evidence-compose reveal"><div class="section-head compact"><div><span class="eyebrow">NEW EVIDENCE</span><h3>Paste a policy or instruction</h3></div></div><label><span class="field-label">MESSAGE</span><textarea class="evidence-text" id="challengeBody">Effective immediately, bank statements are no longer accepted as income proof. Officers must request payslips from gig workers.</textarea></label><div class="form-row"><input class="form-control" id="challengeSource" value="Judge Live Input" aria-label="Evidence source"><select class="form-control" id="challengeAuthority"><option value="2">Operational message</option><option value="3">Team owner</option><option value="4">Senior management</option><option value="5">Official policy owner</option></select></div><div class="compose-actions"><span class="muted">New evidence cannot change policy by itself.</span><button class="btn primary" id="runChallenge">Check impact ${icon('arrow',12)}</button></div><div class="file-drop" id="dropZone">${icon('upload',16)}<div><b>Or drop a file</b><br>.txt · .md · .csv · .json · .eml · .log</div><input type="file" id="fileInput" accept=".txt,.md,.csv,.json,.eml,.log" hidden></div></article>${d?renderChallengeResult(d):renderEmptyEvidenceResult()}<section class="surface memory-panel reveal compact-memory"><div class="memory-head"><b>Current approved evidence</b><span>${state.evidence.length||'—'} sources</span></div><div class="memory-list">${state.evidence.length?state.evidence.slice(0,4).map(e=>`<div class="memory-item"><b>${esc(e.title)}</b><span>${esc(e.source)} · ${esc(e.version||'current')}</span></div>`).join(''):`<div class="memory-item"><b>Loading…</b></div>`}</div></section></section></div>`;
  }

  function renderEmptyEvidenceResult(){ return `<article class="surface result-stage empty-result reveal compact-empty"><div><div class="empty-icon">${icon('spark',20)}</div><h3>Try an unseen message.</h3><p>JurisTwin will compare it with the current official source.</p></div></article>`; }

  function renderChallengeResult(d){
    const reason=d.analysis?.policy_atoms?.reasoning||{}, collision=(reason.collisions||[])[0]||{}, plain=d.analysis?.plain_language||{};
    const verdictLabel=d.verdict==='CONTRADICTION'?'CONFLICT FOUND':d.verdict==='NEEDS_REVIEW'?'NEEDS REVIEW':'ALIGNED';
    return `<article class="surface result-stage reveal compact-result"><div class="result-top"><span class="chip ${d.verdict==='CONTRADICTION'?'red':d.verdict==='NEEDS_REVIEW'?'amber':'green'}">${verdictLabel}</span><span class="chip cyan">LIVE</span></div><h3>${esc(brief(plain.headline||`${fmt(d.blast_radius)} customers may be affected.`,100))}</h3><div class="judge-message-compare compact-judge-compare"><article><small>NEW · ${esc(plain.incoming_source||d.source)}</small><blockquote>“${esc(brief(plain.what_incoming_says||d.body||'',135))}”</blockquote></article><div class="compare-arrow">↕</div><article><small>OFFICIAL · ${esc(plain.canonical_source||d.analysis?.canonical?.source||'Approved evidence')}</small><blockquote>“${esc(brief(plain.what_canonical_says||d.analysis?.canonical?.claim||'',135))}”</blockquote></article></div><div class="plain-answer-grid challenge-answers compact-challenge-answers"><div><small>FOLLOW</small><p>${esc(brief(plain.which_source_wins||'Current approved source stays in force.',92))}</p></div><div><small>AFFECTED</small><p>${esc(brief(plain.customer_impact||`${fmt(d.blast_radius)} customer cases.`,82))}</p></div></div><details class="technical-details compact-details"><summary>Why do they disagree?</summary><p>${esc(brief(plain.why_conflict||collision.explanation||'The instructions point staff to different actions.',180))}</p></details><div class="result-footer"><span class="chip ${d.verdict==='CONTRADICTION'?'red':'green'}">${d.verdict==='CONTRADICTION'?'NOT PUBLISHED':'CHECK COMPLETE'}</span><button class="btn quiet" id="challengeReasoning">Why?</button><button class="btn quiet" id="challengeAIModel">Technical</button><button class="btn quiet" id="challengeToConflict" style="margin-left:auto">Source trail ${icon('arrow',12)}</button></div></article>`;
  }

  async function showAIModelCard(){
    try{
      const d=state.modelCard||await api('/live/ai-model'); state.modelCard=d;
      const b=d.held_out_development_benchmark||{};
      openSheet({title:'Hybrid AI Model Card',subtitle:'Measured learned component + deterministic governance fallback',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">SENTINEL HYBRID POLICY AI</span><h3>Learned proposal. White-box verification. Safe abstention.</h3><p>The learned model proposes policy intent; symbolic atoms, authority controls and abstention verify before any governed action.</p></div><div class="metric-strip model-card-metrics"><div class="metric"><div class="metric-label">TRAINING CORPUS</div><div class="metric-value">${fmt(d.training?.samples||0)}</div><div class="metric-note">curated policy examples</div></div><div class="metric good"><div class="metric-label">DOMAIN MACRO-F1</div><div class="metric-value">${Number(b.domain_macro_f1||0).toFixed(3)}</div><div class="metric-note">held-out development split</div></div><div class="metric good"><div class="metric-label">STANCE MACRO-F1</div><div class="metric-value">${Number(b.stance_macro_f1||0).toFixed(3)}</div><div class="metric-note">held-out development split</div></div><div class="metric"><div class="metric-label">PUBLISH AUTHORITY</div><div class="metric-value">0</div><div class="metric-note">human gate only</div></div></div><div class="sheet-section"><dl class="sheet-kv"><dt>Architecture</dt><dd>${esc(d.architecture||'')}</dd><dt>Abstention</dt><dd>${esc(d.governance?.low_confidence_action||'ABSTAIN / NEEDS_REVIEW')}</dd><dt>Fallback</dt><dd>${esc(d.governance?.fallback||'Deterministic symbolic reasoning remains available offline.')}</dd><dt>Validation boundary</dt><dd>${esc(b.scope_note||'Development benchmark only; not production validation.')}</dd></dl></div>`});
    }catch(e){status(e.message,'error',3000);}
  }

  async function runChallenge(){
    const body=$('#challengeBody')?.value.trim(); if(!body||body.length<8){status('Enter at least 8 characters of policy evidence','error');return;}
    const btn=$('#runChallenge'); if(btn){btn.disabled=true;btn.textContent='Analysing…';}
    try {
      const d=await api('/live/challenge',{method:'POST',body:JSON.stringify({source:$('#challengeSource')?.value||'Judge Live Input',title:'Unseen policy evidence',body,authority:'Judge supplied evidence',authority_level:Number($('#challengeAuthority')?.value||2),sensitivity:'internal'})});
      state.lastChallenge=d;renderShell();status(`${d.verdict} · ${d.blast_radius} cases traced`,'ok',3000);
    } catch(e){status(e.message,'error',3200); if(btn){btn.disabled=false;btn.textContent='Analyse';}}
  }

  async function handleEvidenceFile(file){
    if(!file)return; const allowed=['txt','md','csv','json','eml','log']; const ext=(file.name.split('.').pop()||'').toLowerCase(); if(!allowed.includes(ext)){status('Unsupported file type','error');return;}
    try { status(`Reading ${file.name}…`); const content=await file.text(); const d=await api('/live/evidence-drop',{method:'POST',body:JSON.stringify({filename:file.name,content,mime_type:file.type||'text/plain',authority:'Judge-supplied file',authority_level:2,sensitivity:'internal'})}); state.lastChallenge=d;renderShell();status(`${file.name} analysed · ${d.verdict}`,'ok',3000); } catch(e){status(e.message,'error',3200);}
  }

  async function ensureEvidence(){ if(state.evidence.length)return; try{state.evidence=await api('/memory/sources'); if(state.page==='evidence')renderShell();}catch(e){status(e.message,'error',3000);} }

  function wirePage(){
    if(state.page==='overview'){
      $('#openCritical')?.addEventListener('click',()=>{state.selectedConflict='CF-INCOME-001';navigate(state.conflicts.find(c=>c.conflict_ref==='CF-INCOME-001')?.status==='resolved'?'assurance':'conflict');});
      $('#overviewTwin')?.addEventListener('click',()=>{state.selectedConflict='CF-INCOME-001';state.sim=state.sim?.conflict_ref==='CF-INCOME-001'?state.sim:null;if(state.conflicts.find(c=>c.conflict_ref==='CF-INCOME-001')?.status==='resolved')navigate('assurance');else navigate('twin',()=>setTimeout(runTwin,60));});
      $('#overviewFlow')?.addEventListener('click',finalFlowMenu);$('#overviewPlatform')?.addEventListener('click',platformMenu);$('#overviewGovernance')?.addEventListener('click',()=>navigate('governance'));$('#overviewControls')?.addEventListener('click',()=>navigate('controls'));
      $('#overviewAsk')?.addEventListener('click',()=>runOverviewAnswer(state.overviewRole));
      $('#overviewAIProof')?.addEventListener('click',showOverviewAIProof);$('#overviewSourcePolicy')?.addEventListener('click',showAnswerSourcePolicy);$('#overviewRefresh')?.addEventListener('click',()=>runOverviewAnswer(state.overviewRole));
      $('#overviewQuestion')?.addEventListener('keydown',e=>{if(e.key==='Enter')runOverviewAnswer(state.overviewRole);});
      $$('[data-overview-role]').forEach(b=>b.addEventListener('click',()=>runOverviewAnswer(b.dataset.overviewRole)));
      $$('[data-open-conflict]').forEach(b=>b.addEventListener('click',()=>{state.selectedConflict=b.dataset.openConflict;state.selectedNode=null;navigate('conflict');}));
    }
    if(state.page==='controls'){
      $('#refreshManagerControls')?.addEventListener('click',()=>loadManagerControls(true));
      $$('[data-control-page]').forEach(b=>b.addEventListener('click',()=>{const page=b.dataset.controlPage||'overview';navigate(page,()=>{if(page==='overview'&&b.dataset.controlKey==='authority_majority'&&state.overviewAnswer)setTimeout(showAnswerSourcePolicy,120);});}));
      $$('[data-demo-page]').forEach(b=>b.addEventListener('click',()=>navigate(b.dataset.demoPage||'overview')));
      if(!state.managerControls)setTimeout(()=>loadManagerControls(false),60);
    }
    if(state.page==='conflict'){
      $$('[data-conflict]').forEach(b=>b.addEventListener('click',()=>{state.selectedConflict=b.dataset.conflict;state.selectedNode=null;if(state.sim?.conflict_ref!==state.selectedConflict)state.sim=null;renderShell();}));
      $('#fitGraph')?.addEventListener('click',()=>{drawGraph(true);status('Graph reset','ok');});$('#focusRoot')?.addEventListener('click',focusRoot);$('#conflictTwin')?.addEventListener('click',()=>navigate('twin'));$('#conflictProof')?.addEventListener('click',showProofPack);$('#conflictMessages')?.addEventListener('click',showConflictMessages);requestAnimationFrame(()=>drawGraph(false));
    }
    if(state.page==='twin'){
      $('#runTwin')?.addEventListener('click',runTwin);$('#runTwinEmpty')?.addEventListener('click',runTwin);$('#sendGovernance')?.addEventListener('click',openGovernance);
      $$('[data-twin-conflict]').forEach(b=>b.addEventListener('click',()=>{state.selectedConflict=b.dataset.twinConflict;state.sim=null;state.selectedOption='C';renderShell();}));
      $$('[data-option]').forEach(el=>{el.addEventListener('click',()=>{state.selectedOption=el.dataset.option;renderShell();});el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();state.selectedOption=el.dataset.option;renderShell();}});});
      $$('[data-weight]').forEach(r=>r.addEventListener('input',()=>{state.weights[r.dataset.weight]=Number(r.value);const out=$(`#weight-${r.dataset.weight}`);if(out)out.textContent=`${r.value}%`;}));$('#twinTechnicalProof')?.addEventListener('click',showTwinTechnicalProof);
    }
    if(state.page==='assurance'){
      $('#loadAssurance')?.addEventListener('click',loadAssurance);$('#refreshAssurance')?.addEventListener('click',loadAssurance);$('#proofPack')?.addEventListener('click',showProofPack);$('#proofPackInline')?.addEventListener('click',showProofPack);$('#attackSentinel')?.addEventListener('click',attackSentinel);$('#attackInline')?.addEventListener('click',attackSentinel);$('#rolloutPlan')?.addEventListener('click',showRolloutPlan);$('#rolloutInline')?.addEventListener('click',showRolloutPlan);$('#decisionReplay')?.addEventListener('click',showDecisionReplay);if(!state.assurance&&!state.readiness)setTimeout(loadAssurance,80);
    }
    if(state.page==='governance'){
      $('#refreshGovernance')?.addEventListener('click',()=>loadSecurity(true));
      $('#auditRefresh')?.addEventListener('click',()=>loadSecurity(true));
      $('#openControlCoverage')?.addEventListener('click',()=>navigate('controls'));
      $('#governanceAskLatest')?.addEventListener('click',()=>navigate('overview',()=>setTimeout(()=>runOverviewAnswer(state.overviewRole),90)));
      $('#governanceLiveTest')?.addEventListener('click',()=>navigate('evidence',()=>setTimeout(()=>$('#challengeBody')?.focus(),90)));
      $('#maskedExport')?.addEventListener('click',()=>runCustomerExport('masked'));
      $('#fullExport')?.addEventListener('click',()=>runCustomerExport('full'));
      $$('[data-source-config]').forEach(b=>b.addEventListener('click',()=>showSourceConfig(b.dataset.sourceConfig)));
      if(!state.security)setTimeout(()=>loadSecurity(false),60);
      startSecurityPulse();
    } else { stopSecurityPulse(); }
    if(state.page==='evidence'){
      $('#runChallenge')?.addEventListener('click',runChallenge);$('#challengeToConflict')?.addEventListener('click',()=>navigate('conflict'));$('#challengeAIModel')?.addEventListener('click',showAIModelCard);$('#challengeReasoning')?.addEventListener('click',openReasonerCapability);
      const dz=$('#dropZone'),fi=$('#fileInput');dz?.addEventListener('click',()=>fi?.click());fi?.addEventListener('change',()=>handleEvidenceFile(fi.files?.[0]));dz?.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('dragover');});dz?.addEventListener('dragleave',()=>dz.classList.remove('dragover'));dz?.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('dragover');handleEvidenceFile(e.dataTransfer?.files?.[0]);});ensureEvidence();
    }
  }

  function startHealthPulse(){
    stopHealthPulse();
    const ping=async()=>{try{const t=performance.now();const r=await fetch('/api/system/health',{cache:'no-store'});if(!r.ok)throw new Error();state.liveMs=Math.max(1,Math.round(performance.now()-t));const span=$('#runtime span');if(span)span.textContent=`LIVE · ${state.liveMs} ms`;}catch{const span=$('#runtime span');if(span)span.textContent='RUNTIME CHECK';}};
    ping(); state.healthTimer=setInterval(ping,15000);
  }
  function stopHealthPulse(){if(state.healthTimer){clearInterval(state.healthTimer);state.healthTimer=null;}}

  function updateScrollProgress(){
    const bar=$('#scrollProgressBar');
    if(!bar)return;
    const doc=document.documentElement;
    const max=Math.max(1,doc.scrollHeight-window.innerHeight);
    const pct=Math.max(0,Math.min(100,(window.scrollY/max)*100));
    bar.style.width=`${pct}%`;
  }

  let ambientRaf=0;
  function updateAmbientPointer(e){
    if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    if(ambientRaf)return;
    ambientRaf=requestAnimationFrame(()=>{
      document.documentElement.style.setProperty('--mx',`${e.clientX}px`);
      document.documentElement.style.setProperty('--my',`${e.clientY}px`);
      ambientRaf=0;
    });
  }
  window.addEventListener('scroll',updateScrollProgress,{passive:true});
  window.addEventListener('resize',updateScrollProgress,{passive:true});
  window.addEventListener('pointermove',updateAmbientPointer,{passive:true});

  window.addEventListener('keydown',e=>{
    if(!e.altKey || !state.user)return;
    const key=e.key.toLowerCase();
    if(key==='j'){e.preventDefault();navigate('evidence',()=>setTimeout(()=>$('#challengeBody')?.focus(),80));}
    if(key==='c'){e.preventDefault();navigate('conflict');}
    if(key==='t'){e.preventDefault();navigate('twin');}
    if(key==='a'){e.preventDefault();navigate('assurance');}
    if(key==='g'){e.preventDefault();navigate('governance');}
    if(key==='p'){e.preventDefault();togglePresentation();}
    if(key==='f'){e.preventDefault();finalFlowMenu();}
  });
  window.addEventListener('unhandledrejection',e=>{console.error(e.reason);status(e.reason?.message||'An action was safely contained','error',3200);});

  boot();
  requestAnimationFrame(updateScrollProgress);
})();
