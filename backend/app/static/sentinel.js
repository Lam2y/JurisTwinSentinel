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
  };

  const NAV = [
    ['overview','Overview','home'],
    ['conflict','Conflict Map','network'],
    ['twin','Digital Twin','spark'],
    ['assurance','Assurance','shield'],
    ['evidence','Evidence Lab','file'],
  ];

  const PITCH_OPTION_LABELS = {A:'Take No Action',B:'Update the FSD Only',C:'Align the Complete Process'};

  const META = {
    overview:['Overview','Decision integrity, at a glance'],
    conflict:['Conflict Map','Trace the contradiction and blast radius'],
    twin:['Digital Twin','Stress-test before anything publishes'],
    assurance:['Assurance','Prove the decision is safe to trust'],
    evidence:['Evidence Lab','Challenge JurisTwin with unseen evidence'],
  };

  function esc(v='') { return String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
  function clamp(n,a,b){ return Math.max(a,Math.min(b,n)); }
  function fmt(n){ return Number(n || 0).toLocaleString(); }
  function pct(n){ return `${Math.round(Number(n || 0))}%`; }
  function cap(v=''){ return String(v).replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase()); }
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
    app.innerHTML = `<div style="height:100%;display:grid;place-items:center"><div style="text-align:center;color:#6e7e8a;font-size:10px"><div class="brand-mark" style="margin:0 auto 13px">${icon('shield',19)}</div>Preparing governed workspace…</div></div>`;
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
          <div class="eyebrow">Enterprise decision assurance</div>
          <h1>Stop the business<br>from contradicting itself.</h1>
          <p>JurisTwin detects when authoritative evidence diverges, traces who is exposed, stress-tests the response and keeps a verifiable record of the decision.</p>
          <div class="proof-line"><span><i></i>Explainable</span><span><i></i>Governed</span><span><i></i>Tamper-evident</span></div>
        </div>
        <div class="login-foot">Finals runtime · deterministic local fallback · no cloud dependency</div>
      </section>
      <section class="login-panel">
        <form class="surface login-card" id="loginForm">
          <div class="eyebrow">Protected workspace</div>
          <h2>Sign in</h2>
          <p>Open the live decision-integrity environment.</p>
          <label class="field"><span class="field-label">WORK EMAIL</span><div class="input-shell"><input name="email" type="email" autocomplete="username" value="operations@regulatedbank.com" required></div></label>
          <label class="field"><span class="field-label">PASSWORD</span><div class="input-shell"><input name="password" id="loginPassword" type="password" autocomplete="current-password" value="Finals2026!" required><button id="togglePassword" type="button">SHOW</button></div></label>
          <div class="login-error" id="loginError"></div>
          <button class="btn primary login-submit" type="submit">Enter JurisTwin ${icon('arrow',13)}</button>
          <div class="login-meta"><span>RBAC · DLP · HMAC</span><span>Championship build</span></div>
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
      const [dashboard,conflicts] = await Promise.all([api('/dashboard'),api('/conflicts')]);
      state.dashboard=dashboard; state.conflicts=conflicts; state.loading=false; renderShell(); startHealthPulse();
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
          <div class="top-actions"><div class="runtime" id="runtime"><i></i><span>${state.liveMs?`LIVE · ${state.liveMs} ms`:'LIVE'}</span></div><button class="btn flow-btn" type="button" id="finalFlow">Final Flow</button><button class="btn capability-btn" type="button" id="platformMenu">Platform</button><button class="btn primary challenge-btn" type="button" id="judgeInput">${icon('bolt',14)} Challenge Sentinel</button><button class="btn square" type="button" id="workspaceMenu" aria-label="Workspace menu">${icon('more',18)}</button></div>
        </header>
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
    openSheet({title:'JurisTwin platform',subtitle:'Pitch-deck promises + championship assurance, all live',wide:true,body:`
      <div class="platform-intro"><span class="eyebrow">Decision integrity operating layer</span><h3>Simple story outside. Serious engineering underneath.</h3><p>The final demonstration stays focused. Every capability from the pitch deck and every v4 assurance control remains one click away here.</p></div>
      ${platformGroup('CORE PITCH-DECK CAPABILITIES','The four capabilities judges should remember.',[
        capabilityCard('memory','Secure Enterprise Memory','1 · CONNECT','Teams, Outlook, Gmail, documents and customer data — retrieved by meaning, revealed by role.','file'),
        capabilityCard('twin','Living Decision Digital Twin','2 · EXPOSE','Cross-reference policy, messages, versions and customer impact in one living network.','network'),
        capabilityCard('simulator','White-Box Future Simulator','3 · SIMULATE','Compare three futures across 1,500 stress scenarios before changing the real process.','spark'),
        capabilityCard('bodyguard','AI Bodyguard + Decision Ledger','4 · PROTECT','Monitor approved decisions, contain unsafe changes and keep a replayable proof trail.','shield')
      ])}
      ${platformGroup('CHAMPIONSHIP ASSURANCE','v4 controls that turn the prototype into a defensible enterprise PoC.',[
        capabilityCard('ledger','Decision Ledger','CRYPTOGRAPHIC PROOF','Inspect JT-084, versions, audit trail, compare/merge/rollback/restore and verify the chain.','lock'),
        capabilityCard('reasoner','Hybrid AI Policy Reasoner','LEARNED + WHITE-BOX','A trained local NLP model proposes policy intent; symbolic atoms, authority controls and abstention verify it.','bolt'),
        capabilityCard('rollout','Progressive Rollout','SAFE DELIVERY','Plan CANARY → CONTROLLED → FULL cohorts with explicit rollback conditions.','target'),
        capabilityCard('replay','Decision Replay','TIME MACHINE','Reconstruct who approved what, what propagated and how the decision evolved.','reset'),
        capabilityCard('integrations','Enterprise Connectors','LIVE INGESTION','Operate connector adapters and demonstrate a real HMAC-signed HTTP ingress contract.','network'),
        capabilityCard('assurance','Decision Assurance','GOVERNANCE GATE','Readiness, invariants, proof pack, telemetry and adversarial self-test.','shield'),
        capabilityCard('aimodel','AI Model Card','MEASURED AI','Inspect the learned classifier, held-out development metrics, abstention threshold and publication boundary.','spark')
      ])}
      ${platformGroup('PITCH PROOF','The final three deck messages stay accessible without cluttering navigation.',[
        capabilityCard('operating','Operating Model','CONNECT → PROTECT','Show the exact six-stage final flow and company-wide impact.','arrow'),
        capabilityCard('positioning','Why We Are Different','NOT A CHATBOT','Chatbots answer/retrieve/summarise. Sentinel governs/verifies/simulates.','spark'),
        capabilityCard('pilot','Pilot & Scale','GO TO MARKET','Pilot targets, feasible MVP, truthful runtime stack and commercial path.','target')
      ])}`,
      onOpen:()=>$$('[data-capability]',portal).forEach(btn=>btn.addEventListener('click',()=>openCapability(btn.dataset.capability)))
    });
  }

  async function openCapability(key){
    if(key==='twin'||key==='simulator'){ closeSheet(); navigate('twin'); return; }
    if(key==='reasoner'){ return openReasonerCapability(); }
    if(key==='assurance'){ closeSheet(); navigate('assurance'); return; }
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
    return `<div class="source-pills"><span>Teams</span><span>Outlook</span><span>Gmail</span><span>Documents</span><span>Customer Data</span><i>${icon('arrow',12)}</i><b>AI Classification</b><i>${icon('arrow',12)}</i><b>Vector Evidence Vault</b></div>`;
  }

  async function openMemoryCapability(){
    const sources=await api('/memory/sources');
    const initial=sources.slice(0,8).map(e=>memoryResultRow(e)).join('');
    openSheet({title:'Secure Enterprise Memory',subtitle:'Connect by meaning. Reveal by permission.',wide:true,body:`
      <div class="platform-intro compact"><span class="eyebrow">FEATURE 1 · SECURE ENTERPRISE MEMORY</span><h3>Ask once. Get the governed answer — with proof.</h3><p>JurisTwin retrieves by meaning, checks authority, exposes unresolved conflicts and filters evidence by role before anything is revealed.</p></div>
      ${sourcePills()}
      <section class="verified-answer-panel">
        <div class="verified-answer-head"><div><span class="eyebrow">TRACK 2 · VERIFIED ANSWER</span><h4>Ask enterprise memory in plain language.</h4><p>The learned model routes the question. The answer itself is bound to approved evidence or a Decision Contract — never free-form invention.</p></div><span class="chip green">EVIDENCE-BOUND</span></div>
        <div class="verified-answer-controls"><input id="memoryQuestion" class="form-control" value="Can gig workers use bank statements as income evidence?" aria-label="Ask governed enterprise memory"><button id="memoryAnswer" class="btn primary">Get verified answer</button></div>
        <div id="memoryAnswerResult" class="verified-answer-result idle"><span>Ask a question to see the approved answer, authority and citations.</span></div>
      </section>
      <div class="memory-controls"><div class="role-switch" role="group" aria-label="Role preview"><button class="role-pill active" data-role-preview="manager">Manager · Full evidence</button><button class="role-pill" data-role-preview="officer">Officer · Assigned cases</button><button class="role-pill" data-role-preview="intern">Intern · Redacted</button></div><div class="feature-search"><input id="memoryQuery" class="form-control" value="bank statement income evidence" aria-label="Search enterprise memory"><button id="memorySearch" class="btn">Search evidence</button></div></div>
      <div class="memory-proof-line"><span>Authority</span><span>Sensitivity</span><span>Status</span><span>Version</span><b id="memoryRoleLabel">Preview: Manager</b></div>
      <div id="memoryResults" class="feature-list">${initial}</div>`,onOpen:()=>{
        let preview='manager';
        const run=async()=>{try{const r=await api('/memory/search',{method:'POST',body:JSON.stringify({query:$('#memoryQuery').value,limit:8,filters:{},preview_role:preview})});$('#memoryRoleLabel').textContent=`Preview: ${cap(r.role)}`;$('#memoryResults').innerHTML=r.results.length?r.results.map(memoryResultRow).join(''):'<div class="feature-empty">No governed evidence matched that query.</div>';status(`${cap(r.role)} view · ${r.count} governed results`,'ok');}catch(e){status(e.message,'error',3000);}};
        const ask=async()=>{const q=$('#memoryQuestion')?.value.trim();if(!q||q.length<5){status('Ask a complete policy question','error');return;}const out=$('#memoryAnswerResult');if(out){out.className='verified-answer-result loading';out.innerHTML='<span>Checking learned routing, authority and governed evidence…</span>';}try{const r=await api('/memory/answer',{method:'POST',body:JSON.stringify({question:q,preview_role:preview})});if(out){const tone=r.status==='VERIFIED'?'verified':r.status==='CONFLICT_PRESENT'?'warning':r.status==='RESTRICTED'?'restricted':'review';const cites=(r.citations||[]).slice(0,3).map(c=>`<span>${esc(c.source||'Evidence')} · ${esc(c.version||'current')} · ${esc(c.authority||'governed')}</span>`).join('');out.className=`verified-answer-result ${tone}`;out.innerHTML=`<div class="verified-answer-status"><span class="chip ${r.status==='VERIFIED'?'green':r.status==='CONFLICT_PRESENT'?'amber':r.status==='RESTRICTED'?'red':'cyan'}">${esc(r.status)}</span><small>${esc(cap(r.role||preview))} view · ${Math.round(Number(r.model?.domain_confidence||0)*100)}% domain routing</small></div><strong>${esc(r.answer||'')}</strong>${r.warning?`<p>${esc(r.warning)}</p>`:''}<div class="answer-proof"><b>${esc(r.authority||'Governed authority')}</b><span>${esc(r.source||r.rule_key||'Enterprise Memory')} · ${esc(r.version||'current')}</span>${r.decision_ref?`<code>${esc(r.decision_ref)}</code>`:''}</div>${cites?`<div class="answer-citations"><small>Evidence lineage</small>${cites}</div>`:''}`;}status(`${cap(r.status)} · governed answer returned`,'ok',2600);}catch(e){if(out){out.className='verified-answer-result review';out.innerHTML=`<span>${esc(e.message)}</span>`;}status(e.message,'error',3000);}};
        $$('[data-role-preview]',portal).forEach(b=>b.addEventListener('click',()=>{preview=b.dataset.rolePreview;$$('[data-role-preview]',portal).forEach(x=>x.classList.toggle('active',x===b));run();const out=$('#memoryAnswerResult');if(out&&!out.classList.contains('idle'))ask();}));
        $('#memorySearch')?.addEventListener('click',run);
        $('#memoryAnswer')?.addEventListener('click',ask);
        $('#memoryQuestion')?.addEventListener('keydown',e=>{if(e.key==='Enter')ask();});
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
    openSheet({title:'AI Bodyguard',subtitle:'Protect the decision after approval',wide:true,body:`
      <div class="platform-intro compact"><span class="eyebrow">FEATURE 4 · AI BODYGUARD</span><h3>Approval is not the end of governance.</h3><p>Bodyguard monitors sensitive decisions for unsafe access or modification and gives operators a complete, executable response path.</p></div>
      ${a?bodyguardAlertMarkup(a):'<div class="feature-empty bodyguard-empty"><b>No active incident.</b><br>Publish JT-084, then simulate the pitch-deck modification event.</div>'}
      <div class="feature-actions"><button class="btn danger" id="simulateBodyguard">Simulate “QA-014 modified Credit Policy v4.2”</button><button class="btn" id="openDecisionLedger">Open Decision Ledger</button></div>`,onOpen:()=>{
        $('#simulateBodyguard')?.addEventListener('click',async()=>{try{const x=await api('/bodyguard/simulate-attack',{method:'POST',body:'{}'});status(`Bodyguard contained ${x.alert_ref}`,'ok');await openBodyguardCapability();}catch(e){status(e.message,'error',3200);}});
        $('#openDecisionLedger')?.addEventListener('click',openLedgerCapability);
        $$('[data-bodyguard-action]',portal).forEach(b=>b.addEventListener('click',()=>runBodyguardAction(b.dataset.alert,b.dataset.bodyguardAction)));
      }});
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
    openSheet({title:'Enterprise Connectors',subtitle:'Scattered systems → governed evidence',wide:true,body:`
      <div class="platform-intro compact"><span class="eyebrow">CONNECT</span><h3>${items.filter(x=>x.status==='connected').length}/${items.length} integration adapters connected.</h3><p>Pitch-deck sources are represented through the integration/evidence layer. A separate HMAC-signed webhook demonstrates genuine machine-to-machine HTTP ingress without pretending to be a live Microsoft tenant.</p></div>
      <div class="connector-source-band"><span>Outlook</span><span>Teams</span><span>Gmail</span><span>SharePoint</span><span>ClickUp</span><span>Customer System</span><span>FSD evidence</span></div>
      <div class="integration-grid">${items.map(i=>`<div class="integration-card"><div><b>${esc(i.name)}</b><small>${esc(cap(i.kind))} · ${fmt(i.object_count)} objects</small></div><span class="chip ${i.status==='connected'?'green':'amber'}">${esc(i.status)}</span><em>${esc(i.last_sync_label||'Never')}</em><button class="btn integration-action" data-integration="${esc(i.key)}" data-status="${esc(i.status)}">${i.status==='connected'?'Sync now':'Connect'}</button></div>`).join('')}</div>
      <div class="webhook-proof"><div><span class="eyebrow">REAL NETWORK INGRESS</span><h4>HMAC-SHA256 signed webhook + replay protection</h4><p>Run a second process and send unseen evidence over HTTP into the exact same reasoning pipeline.</p></div><button class="btn primary" id="webhookDetails">Show proof path</button></div>`,onOpen:()=>{
        $$('[data-integration]',portal).forEach(b=>b.addEventListener('click',async()=>{try{const key=b.dataset.integration;const connected=b.dataset.status==='connected';await api(`/integrations/${key}/${connected?'sync':'connect'}`,{method:'POST',body:connected?'{}':JSON.stringify({config:{demo:true}})});status(`${key} ${connected?'synced':'connected'}`,'ok');await openIntegrationsCapability();}catch(e){status(e.message,'error',3000);}}));
        $('#webhookDetails')?.addEventListener('click',showWebhookProof);
      }});
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
    const published=!!demo.decision_published,resolved=demo.conflict_status==='resolved';
    const done=(key)=>key==='CONNECT'||key==='EXPOSE'||((key==='SIMULATE'||key==='RECOMMEND')&&(!!state.sim||published))||(key==='APPROVE'&&published)||(key==='PROTECT'&&published);
    const impact=story.operating_impact||{applications_affected:27,rejected_cases_flagged:1,qa_tests_updated:8,documents_superseded:3,officers_notified:4};
    openSheet({title:'Final Flow',subtitle:'The exact operating model from the pitch deck',wide:true,body:`<div class="platform-intro compact"><span class="eyebrow">FROM ONE CONFLICT TO ONE VERIFIED DECISION</span><h3>${published?'The decision is governed and protected.':'Six steps. One continuous story.'}</h3><p>Every step below is clickable and maps to a live product capability.</p></div><div class="final-flow">${(story.steps||[]).map(x=>`<button class="flow-step ${done(x.key)?'done':''}" data-flow-step="${esc(x.key)}"><i>${x.step}</i><b>${esc(x.key)}</b><span>${esc(x.action)}</span></button>`).join('')}</div><div class="operating-impact"><div><b>${impact.applications_affected}</b><span>applications affected</span></div><div><b>${impact.rejected_cases_flagged}</b><span>rejected case flagged</span></div><div><b>${impact.qa_tests_updated}</b><span>QA tests updated</span></div><div><b>${impact.documents_superseded}</b><span>documents superseded</span></div><div><b>${impact.officers_notified}</b><span>officers notified</span></div></div><div class="flow-thesis">Understand the past. <b>Predict the future.</b> Protect every decision.</div>`,onOpen:()=>$$('[data-flow-step]',portal).forEach(b=>b.addEventListener('click',()=>runFlowStep(b.dataset.flowStep)))});
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

  function showPilotScale(){openSheet({title:'Built for a pilot. Designed to scale.',subtitle:'Pitch-deck commercial path + truthful finals runtime',wide:true,body:`<div class="pilot-grid"><article><span class="eyebrow">PILOT TARGETS</span><ul><li><b>50%</b> faster case investigation</li><li><b>30%</b> fewer duplicate requests</li><li><b>60%</b> faster access to approved decisions</li><li><b>100%</b> evidence-linked final decisions</li><li><b>Zero</b> restricted-data exposure target</li></ul></article><article><span class="eyebrow">FEASIBLE MVP</span><ul><li>1 customer case</li><li>3 employee roles</li><li>1 decision conflict</li><li>3 simulated actions</li><li>1 security incident</li><li>1 version-controlled decision</li></ul></article><article><span class="eyebrow">COMMERCIAL PATH</span><ul><li>JurisTech internal pilot</li><li>Existing banking clients</li><li>Insurance + regulated enterprises</li><li>Enterprise licence</li><li>Implementation fee</li><li>Governance services</li></ul></article></div><div class="runtime-truth"><div><b>Verified finals runtime</b><span>Zero-build SPA · FastAPI · SQLAlchemy · local learned NLP + symbolic reasoner · SQLite/PostgreSQL compatibility · RBAC</span></div><div><b>Pilot target architecture shown in deck</b><span>React · FastAPI · ChromaDB · PostgreSQL · Interpretable ML · RBAC</span></div></div>`});}

  function workspaceMenu(){
    openSheet({title:'Workspace',subtitle:'Finals controls',body:`
      <div class="sheet-section"><h4>Presentation mode</h4><p>Increase supporting text and controls for a projector without changing the application layout.</p><div style="margin-top:14px"><button class="btn ${state.presentation?'primary':''}" id="presentationToggle">${state.presentation?'Presentation mode ON':'Turn on presentation mode'}</button></div></div>
      <div class="sheet-section"><h4>Demo state</h4><p>Reset returns the database to the deterministic finals scenario without restarting the server.</p><div style="margin-top:12px"><button class="btn" id="sheetReset">${icon('reset',14)} Reset finals scenario</button></div></div>
      <div class="sheet-section"><h4>Keyboard shortcuts</h4><dl class="sheet-kv"><dt>Alt + J</dt><dd>Judge input</dd><dt>Alt + C</dt><dd>Conflict map</dd><dt>Alt + T</dt><dd>Digital twin</dd><dt>Alt + A</dt><dd>Assurance</dd><dt>Alt + P</dt><dd>Presentation mode</dd><dt>Alt + F</dt><dd>Final Flow</dd></dl></div>
      <div class="sheet-section"><button class="btn danger" id="sheetLogout">${icon('logout',14)} Sign out</button></div>`,onOpen:()=>{
      $('#presentationToggle')?.addEventListener('click',togglePresentation); $('#sheetReset')?.addEventListener('click',resetDemo); $('#sheetLogout')?.addEventListener('click',()=>logout(true));
    }});
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
      closeSheet(); state.sim=null; state.lastChallenge=null; state.selectedOption='C'; state.graphPositions={}; state.assurance=null; state.readiness=null; state.decisionRefs={}; await refreshCore(); renderShell(); status('Finals scenario restored','ok');
    } catch(e) { status(e.message,'error',3200); }
  }

  function logout(show=true){
    state.token=''; state.user=null; storage.remove('jt_token'); stopHealthPulse(); closeSheet(); if(show) status('Signed out'); renderLogin();
  }

  async function refreshCore(){
    const [dashboard,conflicts] = await Promise.all([api('/dashboard'),api('/conflicts')]); state.dashboard=dashboard; state.conflicts=conflicts;
  }

  function renderSkeleton(){
    return `<div class="loading-page"><div class="skeleton" style="height:38px;width:42%;border-radius:10px"></div><div class="skeleton" style="height:14px;width:54%;border-radius:7px;margin-top:12px"></div><div class="skeleton" style="height:72px;border-radius:14px;margin-top:28px"></div><div class="skeleton" style="height:360px;border-radius:18px;margin-top:14px"></div></div>`;
  }

  function renderPage(){
    if (state.page==='conflict') return renderConflict();
    if (state.page==='twin') return renderTwin();
    if (state.page==='assurance') return renderAssurance();
    if (state.page==='evidence') return renderEvidence();
    return renderOverview();
  }

  function renderOverview(){
    const d=state.dashboard||{}, m=d.metrics||{}, conflicts=d.priority_conflicts||[], i=d.integrity||{};
    const flagship = state.conflicts.find(c=>c.conflict_ref==='CF-INCOME-001') || state.conflicts[0] || {};
    const resolved = flagship.status === 'resolved';
    const focusCount=Number(flagship.affected_customers||27);
    const heroTitle = resolved ? `${focusCount} customers are now protected.` : `${focusCount} customers exposed by one contradiction.`;
    const heroSub = resolved ? 'The governed decision has propagated. AI Bodyguard and the ledger now protect the approved version.' : 'One organisation. Two answers. JurisTwin connects the evidence, exposes the conflict and tests the response before the customer becomes the experiment.';
    return `<div class="page">
      <section class="page-hero reveal"><div><span class="eyebrow">FROM CONFLICT TO CLARITY</span><h2>${esc(heroTitle)}</h2><p>${esc(heroSub)}</p></div><div class="hero-actions"><button class="btn" id="overviewFlow">Final Flow</button><button class="btn primary" id="openCritical">${resolved?'Review proof':'Open critical conflict'} ${icon('arrow',13)}</button></div></section>
      <section class="metric-strip reveal">${metricStrip('Active cases',m.active_cases,'operational')}${metricStrip('Open conflicts',m.decision_conflicts,'need alignment','alert')}${metricStrip('Customers at risk',m.customers_at_risk,'current exposure','alert')}${metricStrip('Protected',m.protected_decisions,'governed decisions','good')}</section>
      <section class="command-grid">
        <article class="surface focus-panel reveal"><div class="focus-top"><span class="chip ${resolved?'green':'red'}">${resolved?'RESOLVED':'CRITICAL'}</span><span class="muted" style="font-size:11px">${esc(flagship.conflict_ref||'CF-INCOME-001')}</span></div><h3>${esc(flagship.name||'Income-document eligibility')}</h3><p>${esc(flagship.root_cause||'Approved bank-statement policy conflicts with stale payslip-only operational guidance.')}</p><div class="impact-line"><div><b>${fmt(focusCount)}</b><span>customers</span></div><div><b>${fmt(flagship.systems_affected||5)}</b><span>systems</span></div><div><b>${Math.round(Number(flagship.confidence||.942)*100)}%</b><span>confidence</span></div></div><button class="btn focus-cta" id="overviewTwin">${resolved?'Inspect decision':'Run Digital Twin'} ${icon('play',12)}</button><div class="story-rail six"><div class="story-step done">Connect</div><div class="story-step done">Expose</div><div class="story-step ${state.sim||resolved?'done':''}">Simulate</div><div class="story-step ${state.sim||resolved?'done':''}">Recommend</div><div class="story-step ${resolved?'done':''}">Approve</div><div class="story-step ${resolved?'done':''}">Protect</div></div></article>
        <aside class="surface integrity-panel reveal"><div class="integrity-head"><div><b>Decision integrity</b><span>Cross-system alignment</span></div><span class="chip ${Number(i.score||0)>=90?'green':'amber'}">${esc(i.threshold||'Watch')}</span></div><div class="integrity-main"><div class="score-ring" style="--score:${Number(i.score||0)}"><strong>${Number(i.score||0)}</strong><small>/100</small></div><div class="integrity-bars">${bar('Evidence',i.evidence_alignment)}${bar('Versions',i.version_consistency)}${bar('Access',i.access_compliance)}${bar('Propagation',i.decision_propagation)}</div></div><button class="btn quiet integrity-flow-btn" id="overviewPlatform">See full platform</button></aside>
        <section class="surface queue-panel reveal"><div class="queue-head"><div><b>Priority queue</b><span> · only what needs attention</span></div><span>${conflicts.length} open</span></div>${conflicts.length?conflicts.slice(0,3).map(c=>`<button class="queue-row" data-open-conflict="${esc(c.conflict_ref)}" type="button" style="border-left:0;border-right:0;border-bottom:0;background:transparent;color:inherit;width:100%;text-align:left;cursor:pointer"><div><b>${esc(c.name)}</b><small>${esc(c.conflict_ref)}</small></div><span class="count">${fmt(c.affected_customers)} affected</span><span class="chip ${String(c.severity).toLowerCase()==='critical'?'red':String(c.severity).toLowerCase()==='high'?'amber':'cyan'}">${esc(c.severity)}</span></button>`).join(''):'<div class="feature-empty"><b>All seeded conflicts governed.</b><br>Decision Replay and Bodyguard retain the complete history.</div>'}</section>
      </section>
    </div>`;
  }

  function metricStrip(label,value,note,cls=''){ return `<div class="metric ${cls}"><div class="metric-label">${esc(label)}</div><div class="metric-value">${fmt(value)}</div><div class="metric-note">${esc(note)}</div></div>`; }
  function bar(label,value){ const v=clamp(Number(value||0),0,100); return `<div class="bar-row"><div class="bar-top"><span>${esc(label)}</span><b>${Math.round(v)}%</b></div><div class="bar-track"><i style="width:${v}%"></i></div></div>`; }

  function renderConflict(){
    const conflicts=state.conflicts||[];const c=conflicts.find(x=>x.conflict_ref===state.selectedConflict)||conflicts[0];
    if(!c) return `<div class="page"><div class="page-hero"><div><h2>No active conflict.</h2><p>The evidence graph is aligned.</p></div></div></div>`;
    state.selectedConflict=c.conflict_ref; state.graph=c.graph;if(!state.selectedNode||!c.graph?.nodes?.some(n=>n.id===state.selectedNode))state.selectedNode=c.graph?.nodes?.find(n=>n.type==='rule')?.id||c.graph?.nodes?.[0]?.id;
    return `<div class="page"><section class="page-hero reveal"><div><div style="display:flex;gap:8px;align-items:center;margin-bottom:10px"><span class="chip ${String(c.severity).toLowerCase()==='critical'?'red':'amber'}">${esc(c.severity)}</span><span class="muted" style="font-size:11px">${esc(c.conflict_ref)}</span></div><h2>See exactly where the organisation disagrees.</h2><p>${esc(c.root_cause)}</p></div><div class="hero-actions"><button class="btn" id="conflictProof">Explain blast radius</button><button class="btn primary" id="conflictTwin">Test resolution ${icon('arrow',13)}</button></div></section><div class="graph-legend reveal"><span class="green-dot">Approved</span><span class="amber-dot">Informal / unlinked</span><span class="red-dot">Conflicting / outdated</span><span class="cyan-dot">Operational impact</span></div><section class="graph-shell reveal"><div class="graph-main"><div class="graph-toolbar"><div class="graph-tabs">${conflicts.map(x=>`<button type="button" class="graph-tab ${x.conflict_ref===c.conflict_ref?'active':''}" data-conflict="${esc(x.conflict_ref)}">${esc(x.name)}</button>`).join('')}</div><div class="graph-actions"><button type="button" class="graph-action" id="focusRoot" title="Focus canonical rule">${icon('target',14)}</button><button type="button" class="graph-action" id="fitGraph" title="Reset graph">${icon('fit',14)}</button></div></div><div class="graph-viewport"><svg id="graphSvg" class="graph-svg" viewBox="0 0 1000 620" preserveAspectRatio="xMidYMid meet" aria-label="Interactive evidence network"></svg></div></div><aside class="graph-inspector"><div class="inspector-label">Selected evidence</div><div id="nodeInspector"></div><div class="drag-hint"><b>Drag any node.</b><br>Source, authority, version and relation remain visible while you trace the conflict.</div></aside></section></div>`;
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
  function nodeDims(n){ return n.type==='rule'?{w:208,h:70}:{w:184,h:62}; }

  function graphNodeSvg(n,p){
    const {w,h}=nodeDims(n); const title=String(nodeTitle(n)); const display=title.length>25?`${title.slice(0,23)}…`:title; const meta=n.source?`${n.source}${n.version?` · ${n.version}`:''}`:(n.type==='rule'?'Canonical rule':'Evidence');
    return `<g class="graph-node ${esc(nodeClass(n))}" data-node-id="${esc(n.id)}" transform="translate(${p.x},${p.y})" tabindex="0"><rect class="graph-node-bg" x="${-w/2}" y="${-h/2}" width="${w}" height="${h}" rx="12"/><circle class="graph-node-dot" cx="${-w/2+15}" cy="${-h/2+16}"/><text class="graph-node-title" x="${-w/2+27}" y="-2">${esc(display)}</text><text class="graph-node-meta" x="${-w/2+15}" y="17">${esc(meta.length>32?`${meta.slice(0,30)}…`:meta)}</text></g>`;
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
    selectGraphNode(id,false);
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
    panel.innerHTML=`<span class="chip ${nodeClass(n)==='conflict'?'red':nodeClass(n)==='approved'?'green':'cyan'}" style="margin-top:12px">${esc(cap(n.type||'evidence'))}</span><h3 class="inspector-title">${esc(nodeTitle(n))}</h3><p class="inspector-copy">${esc(n.claim?cap(n.claim):(n.type==='rule'?'The governed rule at the center of this conflict.':'Enterprise evidence connected to this rule.'))}</p><dl class="inspector-kv"><dt>Source</dt><dd>${esc(n.source||'Governed rule')}</dd><dt>Authority</dt><dd>${esc(n.authority||'System')}</dd><dt>Version</dt><dd>${esc(n.version||'Current')}</dd><dt>Relation</dt><dd>${esc(cap(n.relation||n.status||'root'))}</dd></dl>`;
  }

  function focusRoot(){
    const root=state.graph?.nodes?.find(n=>n.type==='rule'); if(!root)return; state.selectedNode=root.id; drawGraph(true); status('Graph re-centered on canonical rule','ok');
  }

  function renderTwin(){
    const sim=state.sim && state.sim.conflict_ref===state.selectedConflict ? state.sim : null;
    const c=selectedConflictObj();
    return `<div class="page">
      <section class="page-hero reveal"><div><div class="eyebrow">${esc(c?.conflict_ref||'DECISION TWIN')} · ${esc(c?.name||'Select a conflict')}</div><h2>Choose the response that still works when assumptions move.</h2><p>Compare three futures across 1,500 stress scenarios — before anything reaches a customer.</p></div><div class="hero-actions"><button class="btn" id="runTwin">${icon('play',12)} ${sim?'Re-run':'Run'} simulation</button>${sim?`<button class="btn primary" id="sendGovernance">Send to governance ${icon('arrow',13)}</button>`:''}</div></section>
      <div class="graph-tabs reveal" style="margin-bottom:14px">${state.conflicts.map(x=>`<button type="button" class="graph-tab ${x.conflict_ref===state.selectedConflict?'active':''}" data-twin-conflict="${esc(x.conflict_ref)}">${esc(x.name)}</button>`).join('')}</div>
      ${sim?renderTwinResults(sim):renderTwinEmpty()}
    </div>`;
  }

  function renderTwinEmpty(){
    const c=selectedConflictObj();
    return `<section class="surface certificate-panel reveal" style="min-height:330px;display:grid;place-items:center;text-align:center"><div style="max-width:670px"><div class="eyebrow">Decision Digital Twin · ${esc(c?.name||'selected conflict')}</div><h3 style="font-size:32px;margin-top:15px">No black-box recommendation.</h3><p style="font-size:12px;margin:0 auto">JurisTwin exposes the decision priorities, tests every option against uncertainty, and only certifies a recommendation if it remains stable.</p><button class="btn primary" id="runTwinEmpty" style="margin-top:22px">Run 1,500 scenarios ${icon('play',12)}</button></div></section><section class="surface weights-panel reveal" style="margin-top:12px"><h4>Decision priorities</h4><p>Adjust before simulation.</p>${weightRows()}</section>`;
  }

  function weightRows(){ return ['delay','complaint','alignment'].map(k=>`<div class="weight-row"><label>${cap(k)}</label><input type="range" min="10" max="70" value="${state.weights[k]}" data-weight="${k}"><b id="weight-${k}">${state.weights[k]}%</b></div>`).join(''); }

  function renderTwinResults(sim){
    const cert=sim.analysis?.decision_certificate||{};
    const actions=sim.analysis?.recommended_actions||[];
    return `<div class="twin-summary reveal"><span class="chip green">WHITE-BOX · ${esc(cert.status||'ROBUST')}</span><span><strong>${fmt(sim.analysis?.scenario_count||1500)}</strong> scenarios · sensitivity + uncertainty + Pareto checks visible</span></div><section class="decision-lanes reveal">${sim.options.map(o=>`<article class="decision-lane ${state.selectedOption===o.key?'selected':''} ${sim.recommended_option===o.key?'recommended':''}" data-option="${esc(o.key)}" tabindex="0"><div class="lane-key">Option ${esc(o.key)}</div><h3>${esc(sim.analysis?.scenario_profile==='income_document_rule'?(PITCH_OPTION_LABELS[o.key]||cap(o.name)):cap(o.name))}</h3><div class="fit-score">${Number(o.decision_fit).toFixed(1)}<small>/100 fit</small></div><div class="fit-bar"><i style="width:${clamp(Number(o.decision_fit),0,100)}%"></i></div><div class="lane-metrics"><div><b>${Number(o.predicted_delay_days).toFixed(1)}d</b><span>delay</span></div><div><b>${riskLabel(o.complaint_probability)}</b><span>${pct(o.complaint_probability)} complaint</span></div><div><b>${pct(o.policy_alignment)}</b><span>alignment</span></div></div>${o.key==='B'?`<div class="lane-gap">Partial fix · ${fmt(o.applications_affected)} cases remain exposed</div>`:''}${o.key===sim.recommended_option?`<div class="action-chips">${actions.slice(0,5).map(a=>`<span>${esc(a)}</span>`).join('')}</div>`:''}</article>`).join('')}</section><section class="twin-bottom"><article class="surface certificate-panel reveal"><div class="cert-kicker">RECOMMENDED ACTION · WHY OPTION ${esc(sim.recommended_option||'C')}?</div><h3>${esc(sim.analysis?.recommended_title||'Choose the robust complete-process response.')}</h3><p>${esc(sim.analysis?.recommended_rationale||'The recommended option has the lowest weighted decision loss and remains stable when assumptions move.')}</p><div class="cert-strip"><div><b>${fmt(sim.analysis?.scenario_count||1500)}</b><span>scenarios</span></div><div><b>${pct(cert.sensitivity_stability_pct||sim.analysis?.robustness_score)}</b><span>stable tests</span></div><div><b>${Number(cert.worst_case_fit_p10||0).toFixed(1)}</b><span>p10 fit</span></div></div></article><aside class="surface weights-panel reveal"><h4>Decision priorities</h4><p>Transparent weights. No hidden model preference.</p>${weightRows()}</aside></section>`;
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
      openSheet({title:'Governed publication',subtitle:'Nothing publishes unless every control passes',body:`<div class="sheet-section"><div style="display:flex;justify-content:space-between;align-items:center"><span class="chip ${gate.status==='PASS'?'green':'red'}">${esc(gate.status)}</span><span class="sheet-score" style="font-size:34px">${gate.score}<small>/100</small></span></div><h4 style="font-size:19px;margin-top:18px">Publish Option ${esc(state.selectedOption)}?</h4><p>${esc(cap(option?.name||'Selected response'))} becomes the governed resolution only after all assurance checks pass.</p></div><div class="sheet-section"><div class="sheet-list">${gate.checks.map(c=>`<div class="sheet-row"><i>${c.ok?'✓':'!'}</i><div><b>${esc(c.label)}</b><small>${esc(c.detail)}</small></div><span>${c.ok?'PASS':'BLOCK'}</span></div>`).join('')}</div></div>`,footer:`<button class="btn" data-close-sheet type="button">Cancel</button><button class="btn primary" id="confirmPublish" type="button" ${gate.status!=='PASS'||state.selectedOption!=='C'?'disabled':''}>Approve & publish</button>`,onOpen:()=>$('#confirmPublish')?.addEventListener('click',publishDecision)});
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
    if(!a||!r)return `<div class="page"><section class="page-hero reveal"><div><h2>Prove the decision is safe to trust.</h2><p>Verify governance, security, runtime and ledger integrity in one live check.</p></div><div class="hero-actions"><button class="btn primary" id="loadAssurance">Run assurance ${icon('shield',13)}</button></div></section><section class="surface certificate-panel reveal" style="min-height:330px;display:grid;place-items:center;text-align:center"><div><div class="eyebrow">Assurance Control Plane</div><h3 style="font-size:32px">One check before a judge asks.</h3><p>Readiness, governance and runtime controls are evaluated from the live backend.</p></div></section></div>`;
    const gate=a.flagship_governance_gate||{},tel=a.telemetry||{},inv=a.invariants||{};
    return `<div class="page"><section class="page-hero reveal"><div><h2>${r.status==='READY'&&gate.status==='PASS'?'The system is clear to publish.':'A control needs attention.'}</h2><p>These controls are enforced in the backend, not painted onto the interface.</p></div><div class="hero-actions"><button class="btn" id="rolloutPlan">Progressive rollout</button><button class="btn" id="decisionReplay">Decision replay</button><button class="btn" id="proofPack">Decision proof</button><button class="btn danger" id="attackSentinel">Attack Sentinel</button><button class="btn square" id="refreshAssurance" title="Refresh">${icon('reset',14)}</button></div></section><section class="surface assurance-hero reveal"><div class="assurance-score"><strong>${r.score}</strong><small>readiness</small></div><div class="assurance-copy"><span class="chip green">${esc(r.status)}</span><h3>${r.checks.filter(x=>x.ok).length}/${r.checks.length} environment controls verified.</h3><p>Governance gate ${gate.score||0}/100 · runtime success ${Number(tel.success_rate_pct||0).toFixed(0)}% · p95 ${Number(tel.latency_ms?.p95||0).toFixed(1)} ms · safe-state invariants ${esc(inv.status||'HEALTHY')}.</p><div class="assurance-actions"><button class="btn" id="proofPackInline">Build signed proof pack</button><button class="btn" id="rolloutInline">Plan safe rollout</button><button class="btn danger" id="attackInline">Run adversarial test</button></div></div></section><section class="control-columns"><div class="surface control-panel reveal"><div class="control-head"><div><b>Publication controls</b><span> · enforced before policy changes</span></div><span>${gate.checks?.filter(x=>x.ok).length||0}/${gate.checks?.length||0}</span></div>${(gate.checks||[]).map(c=>controlRow(c.label,c.detail,c.ok?'PASS':'BLOCK',c.ok)).join('')}</div><div class="surface control-panel reveal"><div class="control-head"><div><b>Safe-state invariants</b><span> · valid request, valid business state</span></div><span>${esc(inv.status||'')}</span></div>${(inv.checks||[]).map(c=>controlRow(cap(c.key),c.detail,c.ok?'OK':'FAIL',c.ok)).join('')}</div></section></div>`;
  }

  function controlRow(label,detail,stateText,ok=true){ return `<div class="control-row"><i class="control-icon">${ok?'✓':'!'}</i><div><b>${esc(label)}</b><small>${esc(detail)}</small></div><span class="control-state">${esc(stateText)}</span></div>`; }

  async function loadAssurance(){
    try { status('Running assurance controls…'); const [readiness,assurance]=await Promise.all([api('/system/readiness'),api('/assurance/overview')]); state.readiness=readiness;state.assurance=assurance;renderShell();status('Assurance verified','ok'); } catch(e){ status(e.message,'error',3200); }
  }

  async function showProofPack(){
    const c=selectedConflictObj(); if(!c){status('Select a conflict first','error');return;}
    openSheet({title:'Decision assurance proof',subtitle:`${c.name} · signed replayable dossier`,body:`<div class="sheet-section"><p>Building the proof pack from live evidence, reasoning, impact and ledger state…</p></div>`});
    try {
      const detail=await decisionForConflict(c); const ref=detail?.decision?.decision_ref||'';
      const qs=new URLSearchParams({conflict_ref:c.conflict_ref}); if(ref)qs.set('decision_ref',ref);
      const d=await api(`/assurance/proof-pack?${qs.toString()}`); const proof=d.proof||{}, ledger=d.ledger||{}, impact=d.impact||{}, ai=d.ai_assurance||{};
      $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><span class="chip ${d.status==='ASSURED'?'green':'amber'}">${esc(d.status||'ASSURED')}</span><h4 style="font-size:21px;margin-top:15px">One proof-carrying decision dossier.</h4><p>Evidence, AI boundary, reasoning, blast radius, simulation, governance and ledger posture are fingerprinted together and authenticated for later verification.</p></div><div class="sheet-section"><dl class="sheet-kv"><dt>Subject</dt><dd>${esc(d.subject?.decision_ref||d.subject?.conflict_ref||c.conflict_ref)}</dd><dt>AI assurance</dt><dd>${esc(ai.engine||'Hybrid Policy AI')} · publish authority ${ai.model_can_publish===false?'0':'CHECK'}</dd><dt>AI benchmark</dt><dd>Domain F1 ${Number(ai.domain_macro_f1||0).toFixed(3)} · Stance F1 ${Number(ai.stance_macro_f1||0).toFixed(3)}</dd><dt>Blast radius</dt><dd>${impact.affected_cases||0} cases · ${impact.reachable_nodes||0} graph nodes</dd><dt>Ledger</dt><dd>${ledger.verified?'VERIFIED':'CHECK'} · ${ledger.entries||0} chained events</dd><dt>Digest</dt><dd class="mono">${esc(shortHash(proof.bundle_digest))}</dd><dt>Signature</dt><dd class="mono">${esc(shortHash(proof.signature))}</dd><dt>Algorithm</dt><dd>${esc(proof.signature_algorithm||'HMAC-SHA256')}</dd><dt>Key</dt><dd>${esc(proof.key_id||'juristwin-assurance')}</dd></dl></div><div class="proof-verify" id="proofVerifyState"><span class="chip cyan">READY TO VERIFY</span><p>Ask the backend to independently verify this exact digest/signature pair.</p></div><div class="feature-actions"><button class="btn primary" id="verifyThisProof">Verify this proof</button></div>`;
      $('#verifyThisProof')?.addEventListener('click',async()=>{
        const b=$('#verifyThisProof');if(b){b.disabled=true;b.textContent='Verifying…';}
        try{const v=await api('/assurance/verify-proof',{method:'POST',body:JSON.stringify({bundle_digest:proof.bundle_digest,signature:proof.signature})}); const box=$('#proofVerifyState');if(box)box.innerHTML=`<span class="chip ${v.valid?'green':'red'}">${v.valid?'SIGNATURE VALID':'INVALID'}</span><p>${v.valid?'Proof authenticity verified independently by the assurance endpoint.':'The proof did not verify.'}</p>`;status(v.valid?'Proof signature verified':'Proof verification failed',v.valid?'ok':'error',3000);}catch(e){status(e.message,'error',3000);}finally{if(b){b.disabled=false;b.textContent='Verify again';}}
      });
    } catch(e){ $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><p style="color:var(--red)">${esc(e.message)}</p></div>`; }
  }

  async function attackSentinel(){
    openSheet({title:'Attack Sentinel',subtitle:'Live adversarial self-test',body:`<div class="sheet-section"><p>Testing tamper resistance, authorization, input containment and business-state invariants…</p></div>`});
    try {
      const d=await api('/live/red-team',{method:'POST',body:'{}'});
      $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><span class="chip green">${esc(d.status)}</span><div class="sheet-score" style="margin-top:10px">${d.score}<small>/100</small></div><p>${d.passed}/${d.total} controls passed · ${d.state_mutations_persisted} persisted attack mutations · ${d.canonical_decisions_modified} canonical decisions modified.</p></div><div class="sheet-section"><div class="sheet-list">${d.tests.map(t=>`<div class="sheet-row"><i>✓</i><div><b>${esc(t.label)}</b><small>${esc(t.proof)}</small></div><span>PASS</span></div>`).join('')}</div></div>`;
    } catch(e){ $('.sheet-body',portal).innerHTML=`<div class="sheet-section"><p style="color:var(--red)">${esc(e.message)}</p></div>`; }
  }

  function renderEvidence(){
    const d=state.lastChallenge;
    return `<div class="page">
      <section class="page-hero reveal"><div><h2>Give JurisTwin evidence it has never seen.</h2><p>Type a policy change or drop a file. New evidence is quarantined until the governance pipeline resolves it.</p></div></section>
      <section class="evidence-workspace"><article class="surface evidence-compose reveal"><h3>Judge challenge</h3><p>Drop in evidence the system has never seen. JurisTwin will show what conflicts, who is exposed, and why.</p><label><span class="field-label">UNSEEN POLICY EVIDENCE</span><textarea class="evidence-text" id="challengeBody">Effective immediately, bank statements are no longer accepted as income proof. Officers must request payslips from gig workers.</textarea></label><div class="form-row"><input class="form-control" id="challengeSource" value="Judge Live Input" aria-label="Evidence source"><select class="form-control" id="challengeAuthority"><option value="2">Operational evidence · L2</option><option value="3">Functional authority · L3</option><option value="4">Senior authority · L4</option><option value="5">Canonical authority · L5</option></select></div><div class="compose-actions"><span class="muted" style="font-size:8px">Nothing here can silently overwrite canonical policy.</span><button class="btn primary" id="runChallenge">Analyse ${icon('arrow',12)}</button></div><div class="file-drop" id="dropZone">${icon('upload',16)}<div><b style="color:#aabac5">Drop a policy file</b><br>.txt · .md · .csv · .json · .eml · .log</div><input type="file" id="fileInput" accept=".txt,.md,.csv,.json,.eml,.log" hidden></div></article>${d?renderChallengeResult(d):renderEmptyEvidenceResult()}<section class="surface memory-panel reveal"><div class="memory-head"><b>Evidence memory</b><span>${state.evidence.length||'—'} governed sources</span></div><div class="memory-list">${state.evidence.length?state.evidence.slice(0,6).map(e=>`<div class="memory-item"><b>${esc(e.title)}</b><span>${esc(e.source)} · ${esc(e.version||'current')}</span></div>`).join(''):`<div class="memory-item"><b>Loading evidence memory…</b><span>Sources appear without leaving this page.</span></div>`}</div></section></section>
    </div>`;
  }

  function renderEmptyEvidenceResult(){
    return `<article class="surface result-stage empty-result reveal"><div><div class="empty-icon">${icon('spark',20)}</div><h3>No prepared script required.</h3><p>Let a judge type their own policy. JurisTwin will compare it with the highest-authority canonical evidence at runtime.</p></div></article>`;
  }

  function renderChallengeResult(d){
    const reason=d.analysis?.policy_atoms?.reasoning||{}, collision=(reason.collisions||[])[0]||{}, object=collision.object||'BANK_STATEMENT';
    const hybrid=d.analysis?.hybrid_ai||{}, learned=hybrid.learned||{}, arb=hybrid.arbitration||{};
    return `<article class="surface result-stage reveal"><div class="result-top"><span class="chip ${d.verdict==='CONTRADICTION'?'red':d.verdict==='NEEDS_REVIEW'?'amber':'green'}">${esc(d.verdict)}</span><span class="chip cyan">HYBRID AI · ${esc(arb.domain_source||'SAFE FALLBACK')}</span><span class="muted" style="font-size:10px">${Math.round((d.confidence||0)*100)}% confidence</span></div><h3>${fmt(d.blast_radius)} customers in the blast radius.</h3><p>${esc(collision.explanation||d.analysis?.impact_graph?.explanation||'Dependency traversal connected this policy to live customer cases.')}</p><div class="collision-line"><div class="policy-atom"><small>CANONICAL · ${esc(d.analysis?.canonical?.authority||'')}</small><b>${esc(object)} · ${esc(collision.canonical_modality||'PERMITTED')}</b></div><div class="collision-symbol">↔</div><div class="policy-atom"><small>INCOMING · ${esc(d.source)}</small><b>${esc(object)} · ${esc(collision.incoming_modality||'PROHIBITED')}</b></div></div><div class="result-footer"><span class="chip red">QUARANTINED</span><span class="chip cyan">BFS · ${d.analysis?.impact_graph?.reachable_nodes||0} nodes</span><button class="btn quiet" id="challengeAIModel">AI model card</button><button class="btn quiet" id="challengeToConflict" style="margin-left:auto">Open graph ${icon('arrow',12)}</button></div></article>`;
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
      $('#overviewFlow')?.addEventListener('click',finalFlowMenu);$('#overviewPlatform')?.addEventListener('click',platformMenu);
      $$('[data-open-conflict]').forEach(b=>b.addEventListener('click',()=>{state.selectedConflict=b.dataset.openConflict;state.selectedNode=null;navigate('conflict');}));
    }
    if(state.page==='conflict'){
      $$('[data-conflict]').forEach(b=>b.addEventListener('click',()=>{state.selectedConflict=b.dataset.conflict;state.selectedNode=null;if(state.sim?.conflict_ref!==state.selectedConflict)state.sim=null;renderShell();}));
      $('#fitGraph')?.addEventListener('click',()=>{drawGraph(true);status('Graph reset','ok');});$('#focusRoot')?.addEventListener('click',focusRoot);$('#conflictTwin')?.addEventListener('click',()=>navigate('twin'));$('#conflictProof')?.addEventListener('click',showProofPack);requestAnimationFrame(()=>drawGraph(false));
    }
    if(state.page==='twin'){
      $('#runTwin')?.addEventListener('click',runTwin);$('#runTwinEmpty')?.addEventListener('click',runTwin);$('#sendGovernance')?.addEventListener('click',openGovernance);
      $$('[data-twin-conflict]').forEach(b=>b.addEventListener('click',()=>{state.selectedConflict=b.dataset.twinConflict;state.sim=null;state.selectedOption='C';renderShell();}));
      $$('[data-option]').forEach(el=>{el.addEventListener('click',()=>{state.selectedOption=el.dataset.option;renderShell();});el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();state.selectedOption=el.dataset.option;renderShell();}});});
      $$('[data-weight]').forEach(r=>r.addEventListener('input',()=>{state.weights[r.dataset.weight]=Number(r.value);const out=$(`#weight-${r.dataset.weight}`);if(out)out.textContent=`${r.value}%`;}));
    }
    if(state.page==='assurance'){
      $('#loadAssurance')?.addEventListener('click',loadAssurance);$('#refreshAssurance')?.addEventListener('click',loadAssurance);$('#proofPack')?.addEventListener('click',showProofPack);$('#proofPackInline')?.addEventListener('click',showProofPack);$('#attackSentinel')?.addEventListener('click',attackSentinel);$('#attackInline')?.addEventListener('click',attackSentinel);$('#rolloutPlan')?.addEventListener('click',showRolloutPlan);$('#rolloutInline')?.addEventListener('click',showRolloutPlan);$('#decisionReplay')?.addEventListener('click',showDecisionReplay);if(!state.assurance&&!state.readiness)setTimeout(loadAssurance,80);
    }
    if(state.page==='evidence'){
      $('#runChallenge')?.addEventListener('click',runChallenge);$('#challengeToConflict')?.addEventListener('click',()=>navigate('conflict'));$('#challengeAIModel')?.addEventListener('click',showAIModelCard);
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
    if(key==='p'){e.preventDefault();togglePresentation();}
    if(key==='f'){e.preventDefault();finalFlowMenu();}
  });
  window.addEventListener('unhandledrejection',e=>{console.error(e.reason);status(e.reason?.message||'An action was safely contained','error',3200);});

  boot();
  requestAnimationFrame(updateScrollProgress);
})();
