(() => {
  'use strict';

  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const esc = (v='') => String(v).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const fmtPct = v => `${Math.round((Number(v)||0)*100)}%`;
  const fmtMaybePct = v => v === null || v === undefined ? '—' : fmtPct(v);
  const cap = v => String(v||'').replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase());
  const when = v => { try { return new Date(v).toLocaleString([], {dateStyle:'medium',timeStyle:'short'}); } catch { return v||'—'; } };
  const money = v => new Intl.NumberFormat('en-MY',{style:'currency',currency:'MYR',maximumFractionDigits:0}).format(Number(v)||0);
  const TOKEN_KEY='juristwin_v11_token';
  const state={
    token:localStorage.getItem(TOKEN_KEY)||'', user:null, view:'ask', messages:[], gaps:[], overview:null,
    gapDetail:null, controls:null, readiness:null, privacy:null, audit:null, compare:null,
    compareDomain:'income_document_rule', publishing:false, asking:false, ingesting:false, runningTest:false, runningTwin:false, exporting:false, testingTransfer:false,
    patterns:null, metrics:null, compliance:null, risk:null, proof:null, resilienceHistory:null, twin:null, exportManifest:null, transferTest:null
  };
  let toastTimer;

  function toast(message,type='good'){
    const el=$('#toast'); if(!el)return;
    el.textContent=message; el.className=`toast show ${type}`;
    clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.className='toast',3000);
  }

  async function api(path, options={}){
    const controller=new AbortController(); const timeout=setTimeout(()=>controller.abort(),12000);
    const headers={'Content-Type':'application/json',...(options.headers||{})};
    if(state.token)headers.Authorization=`Bearer ${state.token}`;
    try{
      const r=await fetch(`/api${path}`,{...options,headers,signal:controller.signal,cache:'no-store'});
      const data=await r.json().catch(()=>({detail:`Request failed (${r.status})`}));
      if(r.status===401){logout(false);throw new Error('Your session expired. Please sign in again.');}
      if(!r.ok)throw new Error(data.detail||data.errors?.[0]?.message||`Request failed (${r.status})`);
      return data;
    }catch(e){
      if(e.name==='AbortError')throw new Error('JurisTwin took too long to respond. Nothing was published; please retry.');
      throw e;
    }finally{clearTimeout(timeout)}
  }

  const ICONS={
    spark:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l1.2 4.1a6.5 6.5 0 0 0 4.5 4.5L22 12l-4.3 1.4a6.5 6.5 0 0 0-4.5 4.5L12 22l-1.2-4.1a6.5 6.5 0 0 0-4.5-4.5L2 12l4.3-1.4a6.5 6.5 0 0 0 4.5-4.5L12 2z"/></svg>',
    shield:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.8-2.8 8.1-7 10-4.2-1.9-7-5.2-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>',
    publish:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h10l4 4v12H5z"/><path d="M15 4v4h4"/><path d="M8 14l2.2 2.2L16 10.5"/></svg>',
    chart:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V9"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M22 19H2"/></svg>',
    controls:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M4 7h10"/><path d="M18 7h2"/><circle cx="16" cy="7" r="2"/><path d="M4 17h2"/><path d="M10 17h10"/><circle cx="8" cy="17" r="2"/></svg>',
    lock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>',
    compare:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h13"/><path d="M17 4l3 3-3 3"/><path d="M17 17H4"/><path d="M7 14l-3 3 3 3"/></svg>',
    proof:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4-2.6 7.1-8 9-5.4-1.9-8-5-8-9V7l8-4z"/><path d="M9.5 12l1.6 1.7 3.7-4"/></svg>',
    logout:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M10 5H5v14h5"/><path d="M14 8l4 4-4 4"/><path d="M8 12h10"/></svg>',
    send:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M14 7l5 5-5 5"/></svg>',
    user:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg>',
    admin:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.8-2.8 8.1-7 10-4.2-1.9-7-5.2-7-10V6l7-3z"/><path d="M9.5 11.5h5"/><path d="M12 9v5"/></svg>',
    source:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4"/><path d="M9 12h6M9 16h6"/></svg>',
    clock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    audit:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h10v4H7z"/><path d="M5 5H4v16h16V5h-1"/><path d="M8 12h8M8 16h5"/></svg>',
    download:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M5 20h14"/></svg>',
    network:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="6" height="5" rx="1"/><rect x="15" y="15" width="6" height="5" rx="1"/><path d="M9 6.5h6a3 3 0 0 1 3 3V15"/><path d="M15 17.5H9a3 3 0 0 1-3-3V9"/></svg>',
    twin:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="12" r="5"/><circle cx="16" cy="12" r="5"/><path d="M10.5 8h3M10.5 16h3"/></svg>',
    eyeoff:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l18 18"/><path d="M10.6 10.6a2 2 0 0 0 2.8 2.8"/><path d="M9.9 4.2A10.5 10.5 0 0 1 12 4c5 0 9 4 10 8a11.7 11.7 0 0 1-2.2 4.1"/><path d="M6.1 6.1A11.3 11.3 0 0 0 2 12c1 4 5 8 10 8 1.2 0 2.3-.2 3.3-.6"/></svg>',
    check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.2 4.2L19 7"/></svg>'
  };
  const icon=(name,cls='ui-icon')=>`<span class="${cls}" aria-hidden="true">${ICONS[name]||''}</span>`;

  function roleName(){return state.user?.role==='superadmin'?'Superadmin':'Regular User'}
  function initials(){return state.user?.name?.split(/\s+/).map(x=>x[0]).slice(0,2).join('').toUpperCase()||'JT'}
  function brand(){return `<div class="brand" aria-label="JurisTech · JurisTwin Sentinel"><img class="juristech-logo" src="/static/assets/juristech-logo.svg" alt="JurisTech"><span class="brand-divider" aria-hidden="true"></span><div class="brand-copy"><div class="brand-name">JurisTwin <em>Sentinel</em></div><small>Decision Integrity</small></div></div>`}

  async function bootstrap(){
    if(!state.token){renderLogin();return}
    try{
      const s=await api('/auth/session');
      if(!s.authenticated){logout(false);renderLogin();return}
      state.user=s.user; initMessages();
      if(state.user.role==='superadmin')await refreshAdminMeta();
      renderApp();
    }catch{logout(false);renderLogin()}
  }

  function initMessages(){
    if(state.messages.length)return;
    state.messages=[{who:'assistant',answer:state.user?.role==='superadmin'
      ? 'Ask a policy question. I’ll return only the governed answer and its safe source. Anything uncertain becomes a review item below.'
      : 'Hi — ask me a policy or operating-rule question. I’ll give you one governed answer and its source. If the evidence is not safe enough, I’ll send it for review instead of guessing.',sources:[]}];
  }

  function renderLogin(){
    $('#app').innerHTML=`<div class="login-shell">
      <section class="login-hero" aria-labelledby="heroTitle">
        ${brand()}
        <div class="hero-copy">
          <span class="hero-eyebrow"><i></i> Governed AI · Fail-closed decisions · Human publication</span>
          <h1 id="heroTitle">One trusted answer. Full accountability behind it.</h1>
          <p>JurisTwin stops contradictory enterprise knowledge from leaking into frontline decisions. Unknown questions and new evidence are quarantined for governance instead of silently changing policy.</p>
        </div>
        <div class="hero-proof">
          <div class="proof-mini"><b>Contradiction-safe</b><span>Regular users see only governed supporting sources.</span></div>
          <div class="proof-mini"><b>Self-healing</b><span>Human-approved resolutions become reusable semantic decision memory.</span></div>
          <div class="proof-mini"><b>Resilient & auditable</b><span>RBAC, PII minimisation, rollback and HMAC-chained governance history.</span></div>
        </div>
      </section>
      <section class="login-panel"><div class="login-card">
        <h2>Finals demo</h2><p>Choose a role. The two experiences are intentionally different.</p>
        <div class="demo-role-grid">
          <button class="demo-role" data-demo="user"><div class="role-icon" aria-hidden="true">${icon('user','role-svg')}</div><strong>Regular user</strong><span>One page. Ask, receive the governed answer, rate it.</span></button>
          <button class="demo-role" data-demo="admin"><div class="role-icon" aria-hidden="true">${icon('admin','role-svg')}</div><strong>Superadmin</strong><span>Resolve gaps, inspect contradictions, prove security and adoption readiness.</span></button>
        </div>
        <div class="or">or sign in manually</div>
        <form id="loginForm">
          <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" autocomplete="username" placeholder="user@juristech.com" required></div>
          <div class="field"><label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" placeholder="Password" required></div>
          <button class="primary-btn full" type="submit">Sign in</button>
        </form>
        <div class="login-foot"><b>Hackathon demo mode only.</b> Demo password: <span class="mono">Finals2026!</span>. Production deployment replaces these local accounts with enterprise SSO/OIDC.</div>
      </div></section>
    </div>`;
  }

  async function login(email,password){
    try{
      const r=await api('/auth/login',{method:'POST',body:JSON.stringify({email,password})});
      state.token=r.access_token; localStorage.setItem(TOKEN_KEY,state.token); state.user=r.user;
      state.messages=[]; state.view='ask'; initMessages();
      if(state.user.role==='superadmin')await refreshAdminMeta();
      renderApp(); toast(`Signed in as ${roleName()}`);
    }catch(e){toast(e.message,'error')}
  }

  function logout(render=true){
    state.token='';state.user=null;state.messages=[];state.gaps=[];state.overview=null;state.gapDetail=null;
    localStorage.removeItem(TOKEN_KEY); if(render)renderLogin();
  }

  function topbar(){return `<header class="topbar">${brand()}<div class="user-actions"><span class="secure-state">${icon('shield')} Governed session</span><div class="identity-chip"><span class="identity-avatar">${esc(initials())}</span><div><b>${esc(state.user?.name||'')}</b><small>${esc(roleName())}</small></div></div><button class="ghost-btn icon-btn-text" data-action="logout">${icon('logout')}<span>Sign out</span></button></div></header>`}

  function feedbackBlock(m){
    if(m.who!=='assistant'||m.status!=='ANSWERED'||!m.interactionRef)return '';
    if(m.feedback==='helpful')return `<div class="feedback-state good">✓ Marked helpful</div>`;
    if(m.feedback==='review')return `<div class="feedback-state warn">↗ Sent back for superadmin review</div>`;
    return `<div class="feedback-row" aria-label="Answer feedback"><span>Was this useful?</span><button class="feedback-btn" data-feedback="helpful" data-interaction="${esc(m.interactionRef)}">Yes</button><button class="feedback-btn" data-feedback="review" data-interaction="${esc(m.interactionRef)}">Needs review</button></div>`;
  }

  function chatMessage(m){
    if(m.pending)return `<div class="message assistant message-enter"><div class="avatar bot-avatar" aria-hidden="true">${icon('spark')}</div><div class="bubble"><div class="typing" aria-label="JurisTwin is responding"><i></i><i></i><i></i></div></div></div>`;
    const src=(m.sources||[]).map(s=>`<div class="source-card"><span class="source-icon" aria-hidden="true">${icon('source')}</span><div><b>${esc(s.source)} · ${esc(s.title)}</b><span>${esc(s.authority||'Governed source')}${s.version?` · ${esc(s.version)}`:''}</span></div><span class="source-verified" title="Governed source">${icon('check')}</span></div>`).join('');
    const status=m.who==='assistant'&&m.status ? `<div class="answer-status ${m.status==='ANSWERED'?'good':'warn'}">${m.status==='ANSWERED'?`${icon('shield')} Governed answer`:`${icon('clock')} Sent for governance review`}${m.latency?` <span class="status-sep">·</span> ${Number(m.latency).toFixed(0)} ms`:''}</div>`:'';
    return `<div class="message message-enter ${m.who==='user'?'user':'assistant'}">${m.who==='assistant'?`<div class="avatar bot-avatar" aria-hidden="true">${icon('spark')}</div>`:''}<div class="bubble">${status}<div class="answer-copy">${esc(m.answer)}</div>${src?`<div class="source-wrap"><div class="source-label">Verified sources</div>${src}</div>`:''}${feedbackBlock(m)}</div></div>`;
  }

  function chatCard(admin=false){
    return `<div class="chat-card">
      <div class="chat-card-head"><div class="assistant-profile"><span class="assistant-logo">${icon('spark')}</span><div><b>JurisTwin</b><small>Governed policy assistant</small></div></div><span class="online-pill"><i></i> Ready</span></div>
      <div id="chatStream" class="chat-stream" aria-live="polite">${state.messages.map(chatMessage).join('')}</div>
      <div class="chat-compose"><div class="compose-box"><textarea id="askInput" maxlength="1200" rows="1" placeholder="Ask a policy or operating-rule question…" aria-label="Ask JurisTwin" ${state.asking?'disabled':''}></textarea><button id="sendAsk" class="send-btn" aria-label="Send question" ${state.asking?'disabled':''}>${icon('send')}</button></div><div class="compose-meta"><span class="compose-trust">${icon('shield')} ${admin?'Unknown or disputed questions become governed work items automatically.':'JurisTwin abstains when evidence is not safe enough.'}</span><span id="charCount">0 / 1200</span></div></div>
    </div>`;
  }

  function regularView(){
    return `${topbar()}<main id="mainContent" class="regular-main"><section class="chat-page"><div class="page-intro"><div class="kicker"><i class="kicker-dot"></i> Ask JurisTwin</div><h1>One answer. <span class="accent-text">Governed.</span></h1><p>No evidence maze. No contradictory sources. No policy guessing. If JurisTwin cannot defend an answer, it asks for human governance instead.</p><div class="trust-row"><span class="trust-chip">Governed sources only</span><span class="trust-chip">Contradictions withheld</span><span class="trust-chip">Feedback can escalate</span><span class="trust-chip">Safe fallback on uncertainty</span></div></div>${chatCard(false)}<div class="quick-questions" aria-label="Example questions"><button class="quick-question" data-question="Can gig workers use bank statements as income evidence?">Gig-worker income evidence</button><button class="quick-question" data-question="What is the loan restructuring approval threshold?">Loan restructuring threshold</button><button class="quick-question" data-question="What is the customer notification deadline?">Notification deadline</button></div></section></main>`;
  }

  function sidebar(){
    const open=state.overview?.open_gaps||0;
    const nav=(view,label,ico,right='')=>`<button class="nav-btn ${state.view===view?'active':''}" data-view="${view}" ${state.view===view?'aria-current="page"':''}><span class="nav-main">${icon(ico,'nav-icon')}<span class="nav-text">${label}</span></span>${right}</button>`;
    return `<aside class="sidebar">${brand()}
      <nav aria-label="Superadmin navigation">
        <div class="nav-group"><div class="nav-label">Workspace</div>
          ${nav('ask','Ask JurisTwin','spark','<span class="nav-status"></span>')}
          ${nav('safe','Safe to Publish','publish',open?`<span class="badge">${open}</span>`:`<span class="nav-check">${icon('check')}</span>`)}
          ${nav('adoption','Adoption & Impact','chart')}
        </div>
        <div class="nav-group"><div class="nav-label">Trust & Control</div>
          ${nav('controls','Management Controls','controls')}
          ${nav('privacy','Privacy & Data Security','lock')}
        </div>
        <div class="nav-group"><div class="nav-label">Technical Appendix</div>
          ${nav('compare','Compare Evidence','twin')}
          ${nav('auditx','Audit Evidence','audit')}
          ${nav('proof','Judge Proof','proof')}
        </div>
      </nav>
      <div class="sidebar-bottom"><div class="admin-user"><div class="avatar admin-avatar">${esc(initials())}</div><div><b>${esc(state.user?.name)}</b><span>Superadmin · elevated view</span></div></div><div class="sidebar-secure">${icon('shield')} Protected runtime</div></div>
    </aside>`;
  }

  function viewTitle(){return ({ask:'Ask JurisTwin',safe:'Safe to Publish',adoption:'Adoption & Impact',controls:'Management Controls',privacy:'Privacy & Data Security',compare:'Compare Evidence · Digital Twin',auditx:'Audit Evidence',proof:'Judge Proof'})[state.view]||'JurisTwin'}

  function adminTop(){return `<header class="admin-top"><div class="admin-top-title"><span class="admin-top-mark"></span><div><small>JurisTwin Sentinel</small><b>${esc(viewTitle())}</b></div></div><div class="user-actions"><span class="runtime"><i class="runtime-dot"></i> Fail-closed runtime</span><div class="identity-chip compact"><span class="identity-avatar">${esc(initials())}</span><div><b>${esc(state.user?.name||'')}</b><small>Superadmin</small></div></div><button class="ghost-btn icon-btn-text" data-action="logout">${icon('logout')}<span>Sign out</span></button></div></header>`}

  function gapInbox(){
    const open=state.overview?.open_gaps||0;
    if(!open)return `<section class="inbox-strip"><div class="inbox-head"><div><h3>No unresolved knowledge gaps</h3><p>When JurisTwin sees an unseen, weakly supported or disputed question, it appears here automatically.</p></div><span class="count-chip good">Clear</span></div></section>`;
    return `<section class="inbox-strip attention"><div class="inbox-head"><div><h3>${open} item${open===1?'':'s'} waiting for governance</h3><p>Resolve once, publish with source lineage or an explicit uncertainty note, then similar future questions can reuse that governed decision.</p></div><button class="secondary-btn" data-view="safe">Review all</button></div><div class="gap-list">${state.gaps.slice(0,3).map(g=>`<div class="gap-row"><div><b>${esc(g.question)}</b><span>${esc(cap(g.reason))} · seen ${g.occurrence_count}×</span></div><button class="primary-btn" data-solve="${esc(g.gap_ref)}">Solve</button></div>`).join('')}</div></section>`;
  }

  function adminAsk(){
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Frontline answer layer</div><h1>Ask JurisTwin</h1><p>The admin sees the same clean answer experience, then the governance work created by uncertainty appears directly below.</p></div><div class="head-actions"><span class="role-pill">${state.overview?.open_gaps||0} pending</span></div></div><div class="admin-chat-grid">${chatCard(true)}${gapInbox()}</div><div class="quick-questions"><button class="quick-question" data-question="Can gig workers use bank statements as income evidence?">Known governed policy</button><button class="quick-question" data-question="Do QR merchant settlement records count as income proof for self-employed applicants?">Trigger unseen pattern</button></div></main>`;
  }

  function safeList(){
    const patterns=state.patterns||[];
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Human-in-the-loop governance</div><h1>Safe to Publish</h1><p>Every uncertain, disputed or negatively rated decision is quarantined until a superadmin resolves it.</p></div><div class="head-actions"><span class="role-pill">${state.gaps.length} open</span></div></div>
      ${state.gaps.length?`<section class="panel"><div class="panel-head"><div><h3>Knowledge gap queue</h3><div class="panel-sub">Exact duplicates use a SHA-256 fingerprint; strong paraphrases are semantically collapsed so repeated frontline wording becomes one governance task.</div></div></div><div class="gap-list">${state.gaps.map(g=>`<div class="gap-row"><div><b>${esc(g.question)}</b><span>${esc(g.predicted_domain||'Unclassified')} · ${fmtPct(g.domain_confidence)} routing confidence · seen ${g.occurrence_count}× · ${esc(cap(g.reason))}</span></div><button class="primary-btn" data-solve="${esc(g.gap_ref)}">Solve</button></div>`).join('')}</div></section>`:`<div class="empty-state"><div class="empty-icon">✓</div><b>Nothing is waiting for review</b><div>Ask an unseen question, rate an answer “Needs review”, or ingest new evidence to exercise the live governance path.</div></div>`}
      <section class="panel memory-panel"><div class="panel-head"><div><h3>Governed decision memory</h3><div class="panel-sub">Published resolutions are reusable but reversible. Deactivation immediately stops semantic reuse and reopens the linked governance item.</div></div><span class="count-chip">${patterns.filter(p=>p.active).length} active</span></div>${patterns.length?`<div class="memory-list">${patterns.slice(0,8).map(p=>`<div class="memory-row"><div><b>${esc(p.answer)}</b><span>${esc(p.resolution_ref)} · ${esc(p.rule_key||'manual domain')} · threshold ${fmtPct(p.match_threshold)} · ${p.active?'active':'inactive'}</span></div>${p.active?`<button class="danger-btn" data-pattern-deactivate="${esc(p.resolution_ref)}">Deactivate</button>`:'<span class="count-chip">Rolled back</span>'}</div>`).join('')}</div>`:'<div class="empty-state">No governed memory has been published yet.</div>'}</section>
    </main>`;
  }

  function evidenceItem(e,relation){
    const safeToAttach=relation==='support'&&e.approved&&!e.superseded&&String(e.status||'').toLowerCase()==='active';
    const checkbox=safeToAttach?`<div class="source-check"><input type="checkbox" class="publish-source" id="src-${esc(e.evidence_ref)}" value="${esc(e.evidence_ref)}"><label for="src-${esc(e.evidence_ref)}">Attach as verified source lineage</label></div>`:'';
    const scopeLabel=({group_channel:'Approved group channel',formal_approval:'Formal approval',shared_repository:'Shared repository'})[e.source_scope]||cap(e.source_scope||'governed source');
    const relationLabel=relation==='support'?'Supports governed rule':relation==='conflict'?'Contradicts / stale':'Context only';
    return `<article class="evidence-item ${relation}">
      <div class="evidence-top"><div><b>${esc(e.source)} · ${esc(e.title)}</b><span>${esc(e.authority)} · ${esc(e.version||'current')}</span></div><span class="relation-pill ${relation}">${relationLabel}</span></div>
      <div class="evidence-badges"><span>${esc(scopeLabel)}</span><span>${e.approved?'Approved':'Quarantined'}</span><span>Authority ${e.authority_level||0}/5</span><span>Relevance ${fmtPct(e.relevance||0)}</span></div>
      <p class="evidence-copy">${esc(e.body)}</p>
      ${(e.reasons||[]).length?`<div class="evidence-reason"><b>Why it is here</b>${e.reasons.map(r=>`<span>${esc(r)}</span>`).join('')}</div>`:''}
      <div class="evidence-foot"><span>${icon('eyeoff')} PM/DM excluded</span><span>Governance score ${Number(e.governance_score||0).toFixed(2)}</span></div>${checkbox}
    </article>`;
  }

  function evidenceIntake(d){
    const domain=d.predicted_domain||'income_document_rule';
    return `<details class="intake-panel"><summary><span><b>+ Add live governed evidence</b><small>Relevant group channels / formal sources only · PM & DM excluded</small></span><span class="appendix-tag">Quarantine-first</span></summary><div class="intake-body">
      <div class="privacy-callout">${icon('shield')} <div><b>Collection minimisation is enforced before storage.</b><span>Group-channel content must match the selected policy domain. Private/direct messages cannot be selected or ingested.</span></div></div>
      <form id="evidenceForm"><div class="form-grid two"><div class="field"><label for="evSource">Source</label><input id="evSource" required maxlength="100" placeholder="e.g. Teams · Operations Risk"></div><div class="field"><label for="evTitle">Title</label><input id="evTitle" required maxlength="220" placeholder="Evidence title"></div></div>
      <div class="field"><label for="evBody">Relevant evidence text</label><textarea id="evBody" required maxlength="8000" rows="4" placeholder="Paste only the policy-relevant group-channel message or governed source…"></textarea></div>
      <div class="form-grid four"><div class="field"><label for="evScope">Source boundary</label><select id="evScope"><option value="group_channel" selected>Approved group channel</option><option value="formal_approval">Formal approval</option><option value="shared_repository">Shared repository</option></select></div><div class="field"><label for="evDomain">Policy domain</label><select id="evDomain"><option value="income_document_rule" ${domain==='income_document_rule'?'selected':''}>Income documents</option><option value="loan_restructure_rule" ${domain==='loan_restructure_rule'?'selected':''}>Loan restructuring</option><option value="notification_deadline" ${domain==='notification_deadline'?'selected':''}>Notification deadline</option></select></div><div class="field"><label for="evAuthority">Authority</label><input id="evAuthority" maxlength="120" value="Submitted evidence"></div><div class="field"><label for="evLevel">Authority</label><select id="evLevel"><option value="1">1 · Informal</option><option value="2" selected>2 · Operational</option><option value="3">3 · Manager</option><option value="4">4 · Policy owner</option><option value="5">5 · Governing authority</option></select></div></div>
      <div class="intake-actions"><small>PII is rejected. Group chatter that fails the relevance gate is discarded. Accepted evidence remains unapproved until governed.</small><button class="secondary-btn" type="submit" ${state.ingesting?'disabled':''}>${state.ingesting?'Checking boundary…':'Ingest & re-analyse'}</button></div></form>
    </div></details>`;
  }

  function techTrace(t){
    const entries=[
      ['Domain model',t.domain_model],['Router mode',t.router_mode],['Domain prediction',`${t.domain_label||'—'} · ${fmtPct(t.domain_confidence)}`],
      ['Stance signal',`${t.stance_label||'—'} · ${fmtPct(t.stance_confidence)}`],['Retrieval',t.retrieval],['Evidence score',t.governance_score_formula],
      ['White-box verifier',t.symbolic_verifier],['Split-brain gate',t.canonical_split_brain_gate],['Top similarity',fmtPct(t.top_evidence_similarity)],['Publication authority',t.publication_rule],
      ['Privacy boundary',t.privacy_collection_boundary]
    ];
    return `<details class="tech"><summary>Technical trace <span>Show judges the exact decision path</span></summary><div class="trace-grid">${entries.map(([k,v])=>`<div class="trace-item"><b>${esc(k)}</b><span>${esc(v||'—')}</span></div>`).join('')}</div></details>`;
  }

  function safeDetail(){
    const d=state.gapDetail;if(!d)return loadingView('Loading governance analysis…');
    const a=d.analysis||{}, support=a.supporting||[], conflict=a.conflicting||[], context=a.context||[];
    const pct=Math.round((a.recommendation_confidence||0)*100), topSim=fmtPct(a.technical_trace?.top_evidence_similarity||d.top_evidence_similarity||0);
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Decision governance workspace</div><h1>Safe to Publish</h1><p>${esc(d.gap_ref)} · seen ${d.occurrence_count}× · ${esc(cap(d.reason))}</p></div><button class="ghost-btn" data-action="back-gaps">← Back to queue</button></div>
      ${d.status==='resolved'?`<div class="success-banner">Published as ${esc(d.resolution_ref||'governed pattern')}. Similar future questions can reuse the decision while its lineage remains valid.</div>`:''}
      ${a.canonical_conflict?`<div class="critical-banner"><b>Canonical split-brain blocked.</b> Two current approved sources disagree. JurisTwin will not choose a winner automatically.</div>`:''}
      <section class="analysis-hero"><div class="analysis-copy"><div class="kicker">Question under review</div><h2>${esc(d.question)}</h2><p>${a.recommendation?'JurisTwin has an advisory candidate. The superadmin sees the hidden evidence state before deciding what may become organizational memory.':'Coverage is insufficient or disputed. The system needs explicit human governance before anything can be reused.'}</p><div class="hero-badges"><span>${icon('eyeoff')} PM/DM excluded</span><span>${icon('shield')} Human publication only</span><span>${icon('audit')} Audit chained</span></div></div><div class="confidence-ring" style="--pct:${pct}%"><div><span>${pct}%</span><small>advisory confidence</small></div></div></section>
      <section class="admin-only-strip"><div><span>Coverage</span><b>${topSim}</b><small>top semantic evidence match</small></div><div><span>Source boundary</span><b>Minimum required</b><small>approved groups + formal/shared only</small></div><div><span>Visibility</span><b>Superadmin only</b><small>conflicts never leak to regular users</small></div><div><span>Decision owner</span><b>Human</b><small>AI cannot publish policy</small></div></section>
      <div class="metric-grid"><div class="metric"><span>Domain</span><strong class="metric-text">${esc(a.predicted_domain||'Unclassified')}</strong><small>learned router + fallback</small></div><div class="metric"><span>Supporting</span><strong>${support.length}</strong><small>approved/aligned</small></div><div class="metric"><span>Contradicting</span><strong>${conflict.length}</strong><small>stale/incompatible</small></div><div class="metric"><span>Context</span><strong>${context.length}</strong><small>relevant, not authoritative</small></div></div>
      ${a.recommendation?`<section class="recommendation-card"><div class="rec-icon">${icon('spark')}</div><div><span>AI advisory recommendation</span><b>${esc(a.recommendation)}</b><small>Recommendation only — it has zero publication authority until the Superadmin confirms the final wording below.</small></div></section>`:''}
      <div class="evidence-grid"><section class="panel evidence-panel safe-lane"><div class="panel-head"><div><h3>Supporting evidence</h3><div class="panel-sub">Current evidence that can support a governed response.</div></div><span class="count-chip good">${support.length}</span></div>${support.length?support.map(e=>evidenceItem(e,'support')).join(''):'<div class="empty-state">No canonical evidence is strong enough yet.</div>'}</section>
      <section class="panel evidence-panel conflict-lane"><div class="panel-head"><div><h3>Contradictions</h3><div class="panel-sub">Admin-only diagnosis. Never returned as competing user answers.</div></div><span class="count-chip bad">${conflict.length}</span></div>${conflict.length?conflict.map(e=>evidenceItem(e,'conflict')).join(''):'<div class="empty-state">No direct contradiction detected.</div>'}</section></div>
      ${context.length?`<details class="context-drawer"><summary>Other relevant context <span>${context.length}</span><small>Useful for judgement; cannot define policy by itself</small></summary><div class="context-grid">${context.map(e=>evidenceItem(e,'context')).join('')}</div></details>`:''}
      <section class="panel why-panel"><div class="panel-head"><div><h3>Why sources disagree</h3><div class="panel-sub">Concise white-box reasons from policy atoms, authority, version and lifecycle status.</div></div><span class="appendix-tag">Explainable</span></div>${(a.why_sources_disagree||[]).length?`<div class="why-list">${a.why_sources_disagree.slice(0,6).map(x=>`<div class="why-row"><i>!</i><span>${esc(x)}</span></div>`).join('')}</div>`:'<div class="empty-state">No explicit collision. The gap exists because coverage or confidence is still too weak.</div>'}${techTrace(a.technical_trace||{})}</section>
      ${evidenceIntake(d)}
      <section class="panel publish-panel"><div class="panel-head"><div><h3>Human-governed response</h3><div class="panel-sub">One controlled action converts uncertainty into reusable governed memory.</div></div><span class="appendix-tag">Superadmin authority</span></div>
        <div class="publish-grid"><div><div class="field"><label for="finalAnswer">Response to publish</label><textarea id="finalAnswer" placeholder="Write the safe response users should receive next time…">${esc(a.recommendation||'')}</textarea></div><div class="uncertainty-box"><div class="field" style="margin:0"><label for="uncertaintyNote">Uncertainty / exception note</label><textarea id="uncertaintyNote" placeholder="Required when no approved source explicitly supports the response."></textarea></div></div></div>
        <div><div class="field"><label for="matchThreshold">Future pattern threshold</label><select id="matchThreshold"><option value="0.58">58% · broader reuse</option><option value="0.62" selected>62% · balanced</option><option value="0.68">68% · conservative</option><option value="0.75">75% · very strict</option></select></div><div class="decision-rules"><div>${icon('check')} Source lineage revalidated every reuse</div><div>${icon('check')} Contradictory citations rejected server-side</div><div>${icon('check')} No client evidence added to ML training</div><div>${icon('check')} One-click rollback available</div></div></div></div>
        <div class="publish-actions"><small>Publishing records the human owner, selected lineage, threshold and uncertainty state in the tamper-evident ledger.</small><button class="primary-btn" data-action="publish-gap" ${d.status==='resolved'?'disabled':''}>${state.publishing?'Publishing…':d.status==='resolved'?'Already published':'Publish governed response'}</button></div>
      </section>
    </main>`;
  }

  function controlsView(){
    if(!state.controls||!state.readiness)return loadingView('Loading governance controls…');
    const history=state.resilienceHistory||[];
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Risk resilience · 25% rubric proof</div><h1>Management Controls</h1><p>Security and resilience are executable controls, not just claims. Run the self-test live in front of the judges.</p></div><div class="head-actions"><span class="role-pill">Readiness ${state.readiness.score}/100</span><button class="primary-btn" data-action="run-resilience" ${state.runningTest?'disabled':''}>${state.runningTest?'Testing…':'Run live resilience test'}</button></div></div>
      <section class="panel"><h3>Role boundaries</h3><div class="panel-sub">The frontend mirrors backend authorization; hiding a button is never treated as the security boundary.</div><div class="table-scroll"><table class="role-table"><thead><tr><th>Role</th><th>Purpose</th><th>Governance</th><th>Sensitive evidence</th><th>Status</th></tr></thead><tbody>${state.controls.roles.map(r=>`<tr><td><b>${esc(r.display_name)}</b></td><td>${esc(r.description)}</td><td>${r.can_manage_governance?'Allowed':'Blocked'}</td><td>${r.can_view_sensitive_evidence?'Allowed':'Blocked'}</td><td class="${r.enabled?'status-ok':'status-off'}">${r.enabled?'Enabled':'Disabled'}</td></tr>`).join('')}</tbody></table></div></section>
      <div class="control-grid" style="margin-top:14px">${state.controls.shields.map(s=>`<div class="control-card"><div class="control-top"><div><h3>${esc(s.name)}</h3><p>${esc(s.description)}</p></div><label class="switch" aria-label="${esc(s.name)}"><input class="shield-toggle" type="checkbox" data-key="${esc(s.key)}" ${s.enabled?'checked':''} ${['rbac','audit_chain'].includes(s.key)?'disabled':''}><span></span></label></div></div>`).join('')}</div>
      <section class="panel" style="margin-top:14px"><div class="panel-head"><div><h3>Runtime readiness</h3><div class="panel-sub">Calculated from live backend checks; not a hardcoded badge.</div></div><span class="count-chip ${state.readiness.status==='READY'?'good':'bad'}">${esc(state.readiness.status)}</span></div><div class="readiness">${state.readiness.checks.map(c=>`<div class="ready-card ${c.ok?'':'failed'}"><b><i class="ready-dot ${c.ok?'':'bad'}"></i>${esc(c.label)}</b><span>${esc(c.detail)}</span></div>`).join('')}</div></section>
      <section class="panel" style="margin-top:14px"><div class="panel-head"><div><h3>Resilience test history</h3><div class="panel-sub">Every manual self-test is persisted and audit logged.</div></div><span class="count-chip">${history.length} runs</span></div>${history.length?`<div class="run-list">${history.map(r=>`<div class="run-row"><b>${esc(r.run_ref)}</b><span>${esc(r.status)} · ${r.score}/100</span><small>${when(r.created_at)}</small></div>`).join('')}</div>`:'<div class="empty-state">Run the self-test once to create a live resilience record.</div>'}</section>
    </main>`;
  }

  function privacyView(){
    if(!state.privacy||!state.audit||!state.compliance||!state.risk)return loadingView('Loading privacy and data security…');
    const m=state.privacy.metrics||{}, risk=state.risk, b=state.privacy.source_boundary||{}, ds=state.privacy.data_security||{};
    const exportM=state.exportManifest, tx=state.transferTest;
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Privacy · data security · secure exchange</div><h1>Collect less. Protect more.</h1><p>JurisTwin separates policy relevance from surveillance: approved group channels can contribute relevant policy evidence, while private/direct conversations stay outside the collection boundary.</p></div><span class="role-pill">${risk.controlled}/${risk.total} risks controlled</span></div>
      <section class="privacy-boundary-hero"><div><span class="eyebrow">Collaboration privacy boundary</span><h2>Group channel ≠ permission to collect everything.</h2><p>Only policy-relevant content from approved group channels enters the evidence pipeline. PMs, DMs, 1:1 chats and unrelated chatter are blocked before retrieval.</p></div><div class="boundary-stat"><b>0</b><span>private-message sources permitted</span></div></section>
      <div class="boundary-flow"><div class="boundary-node allow"><span>1</span><b>Approved group channel</b><small>or formal/shared governed source</small></div><i>→</i><div class="boundary-node"><span>2</span><b>Relevance gate</b><small>policy domain ≥ ${fmtPct(b.group_chat_relevance_threshold||0.55)}</small></div><i>→</i><div class="boundary-node"><span>3</span><b>PII + lifecycle gate</b><small>reject / quarantine before use</small></div><i>→</i><div class="boundary-node allow"><span>4</span><b>Governed retrieval</b><small>answer or admin review</small></div><div class="boundary-block"><b>PM / DM / 1:1</b><span>Blocked before storage</span></div></div>
      <div class="privacy-grid">${state.privacy.principles.map((p,i)=>`<div class="privacy-card"><div class="privacy-icon">${i+1}</div><h3>${esc(p.title)}</h3><p>${esc(p.detail)}</p></div>`).join('')}</div>
      <section class="data-security-grid">
        <article class="security-action-card"><div class="security-action-head"><div class="security-glyph">${icon('download')}</div><div><span>Customer data export</span><h3>Encrypted before it leaves JurisTwin</h3></div></div><p>The export contains PII-minimised interaction telemetry only. Raw credentials and unmasked prompts are excluded. Encryption uses <b>AES-256-GCM</b>; your passphrase is never stored.</p><form id="exportForm"><div class="field"><label for="exportPass">One-time export passphrase</label><input id="exportPass" type="password" autocomplete="new-password" minlength="10" maxlength="200" placeholder="10+ characters · not persisted"></div><button class="primary-btn full" type="submit" ${state.exporting?'disabled':''}>${state.exporting?'Encrypting…':`${icon('download')} Generate encrypted .jtx export`}</button></form>${exportM?`<div class="security-result good"><b>Encrypted export created</b><span>${exportM.records} interaction records · ${esc(exportM.cipher)} · audit ${esc(exportM.audit_txid)}</span><small>SHA-256 ${esc(exportM.file_sha256)}</small></div>`:''}</article>
        <article class="security-action-card"><div class="security-action-head"><div class="security-glyph">${icon('network')}</div><div><span>System-to-system transfer</span><h3>TLS + API key + HMAC boundary</h3></div></div><p>External systems exchange <b>ciphertext-only</b> packets. Credentials remain server-side; the browser receives only a key fingerprint. Production mode can fail closed on non-HTTPS traffic.</p><div class="transfer-spec"><div><span>Transport</span><b>${ds.https_required?'HTTPS required':'TLS-ready · loopback demo'}</b></div><div><span>Authentication</span><b>Scoped API key + HMAC</b></div><div><span>Key fingerprint</span><b class="mono">${esc(ds.api_key_fingerprint||'—')}</b></div><div><span>Browser access</span><b>${ds.api_key_browser_exposure?'Exposed':'Never exposed'}</b></div></div><button class="secondary-btn full" data-action="transfer-test" ${state.testingTransfer?'disabled':''}>${state.testingTransfer?'Testing boundary…':`${icon('shield')} Run secure-transfer test`}</button>${tx?`<div class="security-result ${tx.status==='PASS'?'good':'bad'}"><b>${esc(tx.status)} · transfer boundary verified</b><span>API key gate ${tx.api_key_gate?'✓':'✕'} · HMAC ${tx.hmac_integrity?'✓':'✕'} · replay ${tx.replay_window?'✓':'✕'}</span><small>Audit ${esc(tx.audit_txid||'—')}</small></div>`:''}</article>
      </section>
      <div class="metric-grid" style="margin-top:14px"><div class="metric"><span>Open review</span><strong>${m.open_review_items||0}</strong><small>quarantined decisions</small></div><div class="metric"><span>Audit entries</span><strong>${m.audit_entries||0}</strong><small>${esc(state.privacy.audit_chain?.algorithm||'verified chain')}</small></div><div class="metric"><span>Interactions</span><strong>${m.interactions||0}</strong><small>PII-minimised telemetry</small></div><div class="metric"><span>Retention</span><strong>${m.resolved_gap_retention_days||'—'}d</strong><small>resolved review data</small></div></div>
      <details class="governance-drawer"><summary>Risk register <span>${risk.controlled}/${risk.total} controlled</span></summary><div class="risk-grid">${risk.risks.map(r=>`<div class="risk-card"><div class="risk-top"><b>${esc(r.risk)}</b><span class="severity ${r.severity.toLowerCase()}">${esc(r.severity)}</span></div><p>${esc(r.control)}</p><span class="status-ok">● ${esc(r.status)}</span></div>`).join('')}</div></details>
      <details class="governance-drawer"><summary>Compliance-by-design mapping <span>Design alignment · not certification</span></summary><div class="compliance-grid">${state.compliance.mappings.map(x=>`<div class="compliance-card"><b>${esc(x.framework)}</b><span>${esc(x.focus)}</span><p>${esc(x.evidence)}</p></div>`).join('')}</div></details>
      <section class="panel audit-preview"><div class="panel-head"><div><h3>Audit evidence preview</h3><div class="panel-sub">Every publish, rollback, export, transfer test and blocked privacy event becomes tamper-evident evidence.</div></div><button class="ghost-btn" data-view="auditx">Open audit appendix →</button></div><div class="audit-list compact">${state.audit.entries.slice(0,6).map(e=>`<div class="audit-row"><b>${esc(e.txid)}</b><span>${esc(e.action)}</span><span>${esc(e.actor)}</span><span class="hash mono">${esc(e.entry_hash)}</span></div>`).join('')}</div></section>
    </main>`;
  }

  function adoptionView(){
    if(!state.metrics)return loadingView('Loading live adoption telemetry…');
    const v=state.metrics.live_validation||{}, o=state.metrics.operational||{}, a=state.metrics.adoption_readiness||{};
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Market feasibility & validation · 20% rubric proof</div><h1>Adoption & Impact</h1><p>Use live usage signals from this running prototype, then separate them clearly from scenario assumptions. No fake “market validation” numbers.</p></div><span class="role-pill">${v.interactions||0} live interactions</span></div>
      <div class="metric-grid"><div class="metric"><span>Answer rate</span><strong>${v.interactions?fmtPct(v.answer_rate):'—'}</strong><small>${v.answered||0} governed answers</small></div><div class="metric"><span>Safe abstention</span><strong>${v.interactions?fmtPct(v.safe_abstention_rate):'—'}</strong><small>${v.review_pending||0} correctly escalated</small></div><div class="metric"><span>Pattern reuse</span><strong>${v.answered?fmtPct(v.pattern_reuse_rate):'—'}</strong><small>${v.pattern_reuse_count||0} answers reused</small></div><div class="metric"><span>Helpfulness</span><strong>${fmtMaybePct(v.helpfulness_rate)}</strong><small>${v.feedback_count||0} user ratings</small></div></div>
      <div class="metric-grid" style="margin-top:12px"><div class="metric"><span>Median latency</span><strong>${Math.round(v.median_latency_ms||0)}ms</strong><small>local end-to-end answer engine</small></div><div class="metric"><span>P95 latency</span><strong>${Math.round(v.p95_latency_ms||0)}ms</strong><small>prototype runtime telemetry</small></div><div class="metric"><span>Open gaps</span><strong>${o.open_gaps||0}</strong><small>governance workload</small></div><div class="metric"><span>Active memory</span><strong>${o.active_patterns||0}</strong><small>human-approved reusable decisions</small></div></div>
      <div class="market-grid"><section class="panel"><h3>Practical deployment path</h3><div class="panel-sub">The prototype is deliberately built to reduce integration risk.</div><div class="fit-list"><div><b>API-first</b><span>Frontend and governance use the same FastAPI boundary external systems can call.</span></div><div><b>Database portable</b><span>${esc(a.database_portable||'—')}</span></div><div><b>Offline-capable core</b><span>${a.internet_required_for_core===false?'No internet required for the core policy engine.':'—'}</span></div><div><b>Identity integration point</b><span>${esc(a.enterprise_sso_integration_point||'—')}</span></div></div><div class="scope-note">${esc(a.note||'')}</div></section>
      <section class="panel"><h3>ROI scenario calculator</h3><div class="panel-sub">Illustrative planning tool only — these inputs are assumptions, not claimed customer results.</div><div class="form-grid three"><div class="field"><label for="roiDecisions">Decisions / day</label><input id="roiDecisions" type="number" min="1" max="100000" value="100"></div><div class="field"><label for="roiMinutes">Minutes saved / decision</label><input id="roiMinutes" type="number" min="0" max="120" step="0.5" value="3"></div><div class="field"><label for="roiCost">Staff cost / hour (RM)</label><input id="roiCost" type="number" min="0" max="10000" step="1" value="40"></div></div><div class="roi-result"><span>Illustrative monthly time value</span><strong id="roiValue">—</strong><small id="roiHours">—</small></div></section></div>
      <section class="panel" style="margin-top:14px"><h3>What validates product feasibility inside this demo?</h3><div class="proof-grid"><div class="proof-card"><b>Real dynamic inputs</b><p>Arbitrary questions, runtime evidence ingestion, feedback and admin resolutions persist through the backend.</p></div><div class="proof-card"><b>Measurable operations</b><p>Answer rate, abstention, reuse, feedback and latency come from actual interactions—not slide placeholders.</p></div><div class="proof-card"><b>Low change-management burden</b><p>Regular users have one task: ask. Governance complexity is isolated to the superadmin role.</p></div><div class="proof-card"><b>Human accountability</b><p>The system assists policy resolution but cannot silently publish or retrain itself on client evidence.</p></div></div></section>
    </main>`;
  }

  function twinPanel(){
    const t=state.twin;
    if(!t)return `<section class="twin-shell"><div class="twin-empty">${icon('twin','twin-big')}<div><h3>Monte Carlo Decision Digital Twin</h3><p>Run 1,500 scenarios to stress-test remediation choices under uncertainty.</p></div><button class="primary-btn" data-action="run-twin">Run 1,500 scenarios</button></div></section>`;
    const cert=t.decision_certificate||{}, weights=t.weights||{};
    return `<section class="twin-shell"><div class="twin-head"><div><span class="twin-eyebrow">${icon('twin')} White-box Decision Digital Twin</span><h2>${esc(t.scenario_label)}</h2><p>${esc(t.validation_note)}</p></div><div class="twin-badge"><b>${t.scenario_count?.toLocaleString?.()||1500}</b><span>Monte Carlo scenarios</span></div></div>
      <div class="twin-controls"><div class="twin-control"><label>Delay exposure <b id="wDelay">${Math.round((weights.delay||.4)*100)}%</b></label><input id="twinDelay" type="range" min="5" max="80" value="${Math.round((weights.delay||.4)*100)}"></div><div class="twin-control"><label>Complaint risk <b id="wComplaint">${Math.round((weights.complaint||.35)*100)}%</b></label><input id="twinComplaint" type="range" min="5" max="80" value="${Math.round((weights.complaint||.35)*100)}"></div><div class="twin-control"><label>Policy alignment <b id="wAlignment">${Math.round((weights.alignment||.25)*100)}%</b></label><input id="twinAlignment" type="range" min="5" max="80" value="${Math.round((weights.alignment||.25)*100)}"></div><button class="secondary-btn" data-action="run-twin" ${state.runningTwin?'disabled':''}>${state.runningTwin?'Simulating…':'Re-run scenarios'}</button></div>
      <div class="twin-options">${(t.options||[]).map(o=>{const rec=o.key===t.recommended_option,u=o.uncertainty||{};return `<article class="twin-option ${rec?'recommended':''}"><div class="twin-option-top"><span>Option ${esc(o.key)}</span>${rec?'<b>Recommended</b>':''}</div><h3>${esc(o.name)}</h3><p>${esc(o.summary)}</p><div class="fit-score"><strong>${o.decision_fit}%</strong><span>decision fit</span></div><div class="fit-bar"><i style="width:${o.decision_fit}%"></i></div><div class="twin-metrics"><div><span>Delay</span><b>${o.predicted_delay_days}d</b></div><div><span>Complaint</span><b>${o.complaint_probability}%</b></div><div><span>Alignment</span><b>${o.policy_alignment}%</b></div><div><span>Affected</span><b>${o.applications_affected}</b></div></div><div class="uncertainty-range"><span>P10 / P50 / P90 fit</span><b>${(u.fit_pct_p10_p50_p90||[]).join(' · ')||'—'}%</b></div></article>`}).join('')}</div>
      <div class="twin-certificate"><div class="certificate-status ${String(cert.status||'').toLowerCase()}"><span>${icon('shield')}</span><div><small>Decision certificate</small><b>${esc(cert.status||'—')}</b></div></div><div><span>Recommended</span><b>Option ${esc(cert.recommended_option||'—')}</b></div><div><span>Worst-case fit (P10)</span><b>${cert.worst_case_fit_p10??'—'}%</b></div><div><span>Sensitivity stability</span><b>${cert.sensitivity_stability_pct??'—'}%</b></div><div><span>Fit margin</span><b>${cert.fit_margin??'—'} pts</b></div><div><span>Pareto</span><b>${cert.pareto_optimal?'Optimal':'Review'}</b></div></div>
      <div class="twin-recommendation"><div><span>Recommended action</span><h3>${esc(t.recommended_title||'')}</h3></div><div class="action-chips">${(t.recommended_actions||[]).map(x=>`<span>${esc(x)}</span>`).join('')}</div></div>
    </section>`;
  }

  function auditEvidenceView(){
    if(!state.audit)return loadingView('Loading audit evidence…');
    const entries=state.audit.entries||[], chain=state.audit.chain||{};
    const dataEvents=entries.filter(e=>/EXPORT|TRANSFER|PRIVATE_MESSAGE|GROUP_CHAT/i.test(e.action));
    const governanceEvents=entries.filter(e=>/PUBLISH|MEMORY|EVIDENCE|CONFLICT|FEEDBACK/i.test(e.action));
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Appendix · audit log slides</div><h1>Audit Evidence</h1><p>Three judge-ready views of accountability: who acted, whether history was tampered with, and how sensitive data moved.</p></div><span class="appendix-tag">Live ledger · ${entries.length} shown</span></div>
      <section class="audit-slide"><div class="slide-no">01</div><div class="slide-copy"><span>Accountability</span><h2>Who did what — and when?</h2><p>Governance actions are recorded with an immutable transaction ID, actor, action, timestamp and cryptographic link to previous history.</p></div><div class="slide-live-list">${entries.slice(0,6).map(e=>`<div><b>${esc(e.txid)}</b><span>${esc(e.action)}</span><small>${esc(e.actor)} · ${when(e.created_at)}</small></div>`).join('')}</div></section>
      <section class="audit-slide dark"><div class="slide-no">02</div><div class="slide-copy"><span>Tamper evidence</span><h2>${chain.ok?'Chain verified.':'Chain integrity warning.'}</h2><p>The ledger uses ${esc(chain.algorithm||'HMAC-SHA256 chaining')}. A database-only attacker cannot silently rewrite old decisions and recompute a valid chain without the server-held key.</p><div class="audit-proof-row"><div><span>Entries</span><b>${chain.entries||0}</b></div><div><span>Errors</span><b>${(chain.errors||[]).length}</b></div><div><span>Head hash</span><b class="mono">${esc((chain.head_hash||'—').slice(0,18))}…</b></div></div></div><div class="chain-visual">${entries.slice(0,5).reverse().map((e,i)=>`<div><span>${esc(e.txid)}</span><i></i><b>${esc((e.entry_hash||'').slice(0,10))}</b></div>`).join('')}</div></section>
      <section class="audit-slide"><div class="slide-no">03</div><div class="slide-copy"><span>Data lifecycle</span><h2>Export and transfer leave evidence too.</h2><p>Encrypted customer exports, system-transfer security tests, accepted transfers and privacy blocks are logged without storing passwords, API keys or plaintext customer payloads.</p></div><div class="audit-event-grid"><div><b>${dataEvents.length}</b><span>data-security events</span><small>${dataEvents.slice(0,4).map(x=>esc(x.action)).join(' · ')||'Generate an encrypted export or run the transfer test to populate this proof.'}</small></div><div><b>${governanceEvents.length}</b><span>governance events</span><small>publish · rollback · evidence · conflicts</small></div></div></section>
      <section class="panel"><div class="panel-head"><div><h3>Live audit records</h3><div class="panel-sub">Appendix detail — use only if judges ask for a specific transaction.</div></div><span class="count-chip ${chain.ok?'good':'bad'}">${chain.ok?'HMAC chain verified':'Attention'}</span></div><div class="audit-list">${entries.map(e=>`<div class="audit-row"><b>${esc(e.txid)}</b><span>${esc(e.action)}</span><span>${esc(e.actor)}</span><span class="hash mono">${esc(e.entry_hash)}</span></div>`).join('')}</div></section>
    </main>`;
  }

  function compareView(){
    if(!state.compare)return loadingView('Loading evidence comparison…');
    const c=state.compare,sup=c.supporting||[],x=c.conflicting||[],ctx=c.context||[];
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Appendix · contradiction + simulation engine</div><h1>Compare Evidence</h1><p>Inspect why evidence disagrees, then stress-test remediation choices with the Monte Carlo Decision Digital Twin.</p></div><div class="compare-picker"><span class="appendix-tag">Appendix</span><select id="compareDomain" aria-label="Evidence domain"><option value="income_document_rule" ${state.compareDomain==='income_document_rule'?'selected':''}>Income documents</option><option value="loan_restructure_rule" ${state.compareDomain==='loan_restructure_rule'?'selected':''}>Loan restructuring</option><option value="notification_deadline" ${state.compareDomain==='notification_deadline'?'selected':''}>Notification deadline</option></select></div></div>
      ${twinPanel()}
      <div class="section-divider"><span>Evidence state behind the simulation</span></div>
      <div class="compare-summary"><div class="compare-box"><span>Supports</span><b>${sup.length}</b></div><div class="compare-box"><span>Conflicts / stale</span><b>${x.length}</b></div><div class="compare-box"><span>Context</span><b>${ctx.length}</b></div></div>
      <div class="evidence-grid"><section class="panel"><div class="panel-head"><div><h3>Governed / aligned</h3><div class="panel-sub">What can safely support the answer.</div></div><span class="count-chip good">${sup.length}</span></div>${sup.map(e=>evidenceItem(e,'support')).join('')||'<div class="empty-state">No supporting evidence</div>'}</section><section class="panel"><div class="panel-head"><div><h3>Contradicting / stale</h3><div class="panel-sub">What regular users never see as a competing answer.</div></div><span class="count-chip bad">${x.length}</span></div>${x.map(e=>evidenceItem(e,'conflict')).join('')||'<div class="empty-state">No contradictions</div>'}</section></div>
      <section class="panel why-panel"><h3>Why sources disagree</h3><div class="why-list">${(c.why_sources_disagree||[]).slice(0,6).map(x=>`<div class="why-row"><i>!</i><span>${esc(x)}</span></div>`).join('')||'<div class="empty-state">No collision</div>'}</div>${techTrace(c.technical_trace||{})}</section>
    </main>`;
  }

  function proofView(){
    if(!state.proof)return loadingView('Loading technical proof…');
    const p=state.proof, card=p.model_card||{}, bench=card.held_out_development_benchmark||{}, training=card.training||{};
    return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">Appendix · Defensibility & Q&A</div><h1>Judge Proof</h1><p>A compact screen for “is it hardcoded?”, “where is the ML?”, “what can fail?”, and “what are your limitations?”</p></div><span class="appendix-tag">${esc(p.version||'Mastery')}</span></div>
      <section class="panel"><div class="panel-head"><div><h3>Architecture judges can defend</h3><div class="panel-sub">Each layer has a distinct job; no LLM is trusted as the final policy authority.</div></div></div><div class="architecture-chain">${(p.architecture||[]).map((x,i)=>`<div class="arch-step"><span>${i+1}</span><b>${esc(x)}</b></div>`).join('')}</div></section>
      <div class="metric-grid" style="margin:14px 0"><div class="metric"><span>Live resilience</span><strong>${p.verification?.live_resilience_score??'—'}/100</strong><small>${p.verification?.all_live_checks_passing?'all live checks passing':'attention required'}</small></div><div class="metric"><span>Live controls checked</span><strong>${p.verification?.live_resilience_checks??'—'}</strong><small>backend-evaluated resilience controls</small></div><div class="metric"><span>Regression suite</span><strong>25</strong><small>automated finals tests</small></div><div class="metric"><span>Publication authority</span><strong style="font-size:18px">Human</strong><small>model cannot publish policy</small></div></div>
      <div class="proof-split"><section class="panel"><h3>Proof it is not one hardcoded story</h3><div class="check-list">${(p.not_hardcoded_proofs||[]).map(x=>`<div><i>✓</i><span>${esc(x)}</span></div>`).join('')}</div></section><section class="panel"><h3>Boundaries we state openly</h3><div class="limit-list">${(p.limits||[]).map(x=>`<div><i>!</i><span>${esc(x)}</span></div>`).join('')}</div></section></div>
      <section class="panel" style="margin-top:14px"><div class="panel-head"><div><h3>Learned component model card</h3><div class="panel-sub">Transparent development benchmark—not presented as production validation.</div></div><span class="count-chip good">${esc(card.status||'—')}</span></div><div class="metric-grid"><div class="metric"><span>Corpus</span><strong>${training.samples||0}</strong><small>${esc(training.corpus_type||'')}</small></div><div class="metric"><span>Domain accuracy</span><strong>${fmtPct(bench.domain_accuracy)}</strong><small>held-out development split</small></div><div class="metric"><span>Domain macro-F1</span><strong>${fmtPct(bench.domain_macro_f1)}</strong><small>held-out development split</small></div><div class="metric"><span>Internet</span><strong style="font-size:18px">${training.internet_required?'Required':'Not required'}</strong><small>core model runtime</small></div></div></section>
    </main>`;
  }

  function loadingView(label){return `<main id="mainContent" class="admin-content"><div class="page-head"><div><div class="kicker">JurisTwin Sentinel</div><h1>${esc(label)}</h1></div></div><div class="skeleton block"></div><div class="skeleton line" style="width:70%"></div><div class="skeleton line" style="width:45%"></div></main>`}

  function adminContent(){
    if(state.view==='ask')return adminAsk();
    if(state.view==='safe')return state.gapDetail?safeDetail():safeList();
    if(state.view==='adoption')return adoptionView();
    if(state.view==='controls')return controlsView();
    if(state.view==='privacy')return privacyView();
    if(state.view==='compare')return compareView();
    if(state.view==='auditx')return auditEvidenceView();
    if(state.view==='proof')return proofView();
    return adminAsk();
  }

  function renderApp(){
    if(!state.user){renderLogin();return}
    if(state.user.role!=='superadmin'){$('#app').innerHTML=regularView();afterRender();return}
    $('#app').innerHTML=`<div class="admin-shell">${sidebar()}<div class="admin-main">${adminTop()}${adminContent()}</div></div>`;
    afterRender();
  }

  function afterRender(){
    const stream=$('#chatStream'); if(stream)requestAnimationFrame(()=>stream.scrollTop=stream.scrollHeight);
    const input=$('#askInput'); if(input){
      input.addEventListener('input',()=>{const c=$('#charCount');if(c)c.textContent=`${input.value.length} / 1200`;autoGrow(input)});
      input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submitAsk()}});
    }
    const roiInputs=['#roiDecisions','#roiMinutes','#roiCost'].map(s=>$(s)).filter(Boolean);
    if(roiInputs.length){roiInputs.forEach(x=>x.addEventListener('input',updateRoi));updateRoi()}
    const twinMap=[['#twinDelay','#wDelay'],['#twinComplaint','#wComplaint'],['#twinAlignment','#wAlignment']];
    twinMap.forEach(([i,l])=>{const input=$(i),label=$(l);if(input&&label)input.addEventListener('input',()=>label.textContent=`${input.value}%`)})
  }

  function autoGrow(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,150)+'px'}

  function updateRoi(){
    const d=Number($('#roiDecisions')?.value||0), m=Number($('#roiMinutes')?.value||0), c=Number($('#roiCost')?.value||0);
    const hours=d*m/60*22, value=hours*c;
    const val=$('#roiValue'), h=$('#roiHours'); if(val)val.textContent=money(value); if(h)h.textContent=`${Math.round(hours)} staff-hours/month in this scenario`;
  }

  async function submitAsk(questionOverride){
    if(state.asking)return;
    const input=$('#askInput');const q=(questionOverride||input?.value||'').trim();
    if(q.length<3){toast('Ask a complete question first.','error');return}
    if(input){input.value='';autoGrow(input)}
    state.asking=true; state.messages.push({who:'user',answer:q,sources:[]},{who:'assistant',pending:true});renderApp();
    try{
      const r=await api('/ask',{method:'POST',body:JSON.stringify({question:q})});
      state.messages[state.messages.length-1]={who:'assistant',answer:r.answer,sources:r.sources||[],status:r.status,interactionRef:r.interaction_ref,latency:r.latency_ms};
      state.asking=false;
      if(state.user.role==='superadmin')await refreshAdminMeta();
      renderApp();
      if(r.status==='REVIEW_PENDING')toast('Safely quarantined for superadmin review.');
    }catch(e){
      state.asking=false;state.messages[state.messages.length-1]={who:'assistant',answer:`I couldn't complete that request safely: ${e.message}`,sources:[]};renderApp();toast(e.message,'error');
    }
  }

  async function submitFeedback(ref,helpful){
    const m=state.messages.find(x=>x.interactionRef===ref); if(!m||m.feedback)return;
    try{
      const r=await api('/ask/feedback',{method:'POST',body:JSON.stringify({interaction_ref:ref,helpful})});
      m.feedback=helpful?'helpful':'review'; renderApp();
      toast(helpful?'Thanks — feedback recorded.':r.escalated?'Answer sent back for governance review.':'Feedback recorded.');
    }catch(e){toast(e.message,'error')}
  }

  async function refreshAdminMeta(){
    if(state.user?.role!=='superadmin')return;
    try{[state.overview,state.gaps]=await Promise.all([api('/admin/overview'),api('/admin/gaps?status=open')]);}catch(e){toast(e.message,'error')}
  }

  async function switchView(view){
    state.view=view;state.gapDetail=null;renderApp();
    try{
      if(view==='safe'){await refreshAdminMeta();state.patterns=await api('/admin/patterns');}
      if(view==='adoption')state.metrics=await api('/admin/metrics');
      if(view==='controls')[state.controls,state.readiness,state.resilienceHistory]=await Promise.all([api('/governance/controls'),api('/governance/readiness'),api('/governance/resilience-history')]);
      if(view==='privacy')[state.privacy,state.audit,state.compliance,state.risk]=await Promise.all([api('/governance/privacy'),api('/governance/audit?limit=32'),api('/governance/compliance'),api('/governance/risk-register')]);
      if(view==='compare'){[state.compare,state.twin]=await Promise.all([api(`/admin/compare/${state.compareDomain}`),api(`/admin/compare/${state.compareDomain}/simulate`,{method:'POST',body:JSON.stringify({delay:.40,complaint:.35,alignment:.25})})]);}
      if(view==='auditx')state.audit=await api('/governance/audit?limit=60');
      if(view==='proof')state.proof=await api('/governance/technical-proof');
    }catch(e){toast(e.message,'error')}
    renderApp();
  }

  async function solveGap(ref){
    state.view='safe';state.gapDetail=null;renderApp();
    try{state.gapDetail=await api(`/admin/gaps/${encodeURIComponent(ref)}`);renderApp()}catch(e){toast(e.message,'error');await switchView('safe')}
  }

  async function publishGap(){
    if(!state.gapDetail||state.publishing)return;
    const answer=$('#finalAnswer')?.value.trim()||'';if(answer.length<3){toast('Write the response you want JurisTwin to publish.','error');return}
    const source_refs=$$('.publish-source:checked').map(x=>x.value);const uncertainty_note=$('#uncertaintyNote')?.value.trim()||null;const match_threshold=Number($('#matchThreshold')?.value||0.62);
    state.publishing=true;renderApp();
    try{
      const r=await api(`/admin/gaps/${encodeURIComponent(state.gapDetail.gap_ref)}/publish`,{method:'POST',body:JSON.stringify({answer,source_refs,uncertainty_note,match_threshold})});
      toast(`Published ${r.resolution_ref}`);await refreshAdminMeta();state.patterns=await api('/admin/patterns');state.gapDetail=await api(`/admin/gaps/${encodeURIComponent(state.gapDetail.gap_ref)}`);state.publishing=false;renderApp();
    }catch(e){state.publishing=false;renderApp();toast(e.message,'error')}
  }

  async function ingestEvidence(form){
    if(!state.gapDetail||state.ingesting)return;
    const payload={
      source:$('#evSource')?.value.trim(), title:$('#evTitle')?.value.trim(), body:$('#evBody')?.value.trim(),
      rule_key:$('#evDomain')?.value, authority:$('#evAuthority')?.value.trim()||'Submitted evidence', authority_level:Number($('#evLevel')?.value||2), sensitivity:'internal', source_scope:$('#evScope')?.value||'group_channel'
    };
    if(!payload.source||!payload.title||!payload.body){toast('Complete the source, title and evidence text.','error');return}
    state.ingesting=true; const button=form.querySelector('button[type="submit"]');if(button){button.disabled=true;button.textContent='Ingesting…'}
    try{
      const r=await api('/admin/evidence/ingest',{method:'POST',body:JSON.stringify(payload)});
      state.gapDetail=await api(`/admin/gaps/${encodeURIComponent(state.gapDetail.gap_ref)}`);state.ingesting=false;renderApp();
      toast(r.duplicate?'That evidence already exists.':r.collisions?.length?`Quarantined ${r.evidence_ref}: ${r.collisions.length} conflict signal(s).`:`Quarantined ${r.evidence_ref} and re-analysed.`);
    }catch(e){state.ingesting=false;if(button){button.disabled=false;button.textContent='Ingest & re-analyse'}toast(e.message,'error')}
  }

  async function deactivatePattern(ref){
    try{
      const r=await api(`/admin/patterns/${encodeURIComponent(ref)}`,{method:'PATCH',body:JSON.stringify({active:false,reason:'Superadmin rollback from Safe to Publish'})});
      toast(r.reopened_gap?`Rolled back and reopened ${r.reopened_gap}.`:'Decision memory deactivated.');
      await refreshAdminMeta();state.patterns=await api('/admin/patterns');renderApp();
    }catch(e){toast(e.message,'error')}
  }

  async function runResilience(){
    if(state.runningTest)return;state.runningTest=true;renderApp();
    try{
      const r=await api('/governance/resilience-test',{method:'POST'});toast(`Resilience test ${r.status}: ${r.score}/100`);
      [state.readiness,state.resilienceHistory]=await Promise.all([api('/governance/readiness'),api('/governance/resilience-history')]);state.runningTest=false;renderApp();
    }catch(e){state.runningTest=false;renderApp();toast(e.message,'error')}
  }

  async function toggleShield(input){
    const before=!input.checked;
    try{await api(`/governance/shields/${encodeURIComponent(input.dataset.key)}`,{method:'PATCH',body:JSON.stringify({enabled:input.checked})});toast('Security control updated');[state.controls,state.readiness]=await Promise.all([api('/governance/controls'),api('/governance/readiness')]);renderApp()}catch(e){input.checked=before;toast(e.message,'error')}
  }

  async function changeCompare(value){state.compareDomain=value;state.compare=null;state.twin=null;renderApp();try{[state.compare,state.twin]=await Promise.all([api(`/admin/compare/${value}`),api(`/admin/compare/${value}/simulate`,{method:'POST',body:JSON.stringify({delay:.40,complaint:.35,alignment:.25})})]);renderApp()}catch(e){toast(e.message,'error')}}

  async function runTwin(){
    if(state.runningTwin)return;state.runningTwin=true;renderApp();
    const payload={delay:Number($('#twinDelay')?.value||40)/100,complaint:Number($('#twinComplaint')?.value||35)/100,alignment:Number($('#twinAlignment')?.value||25)/100};
    try{state.twin=await api(`/admin/compare/${state.compareDomain}/simulate`,{method:'POST',body:JSON.stringify(payload)});state.runningTwin=false;renderApp();toast(`Digital Twin: ${state.twin.scenario_count} scenarios · Option ${state.twin.recommended_option} recommended`)}catch(e){state.runningTwin=false;renderApp();toast(e.message,'error')}
  }

  async function exportCustomerData(){
    if(state.exporting)return;const pass=$('#exportPass')?.value||'';if(pass.length<10){toast('Use an export passphrase with at least 10 characters.','error');return}
    state.exporting=true;renderApp();
    try{const r=await api('/governance/customer-export',{method:'POST',body:JSON.stringify({passphrase:pass,include_feedback:true})});const raw=atob(r.content_base64);const bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);const blob=new Blob([bytes],{type:'application/octet-stream'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=r.filename;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);state.exportManifest=r.manifest;[state.privacy,state.audit]=await Promise.all([api('/governance/privacy'),api('/governance/audit?limit=32')]);state.exporting=false;renderApp();toast(`Encrypted export created · ${r.manifest.audit_txid}`)}catch(e){state.exporting=false;renderApp();toast(e.message,'error')}
  }

  async function runTransferTest(){
    if(state.testingTransfer)return;state.testingTransfer=true;renderApp();
    try{state.transferTest=await api('/governance/transfer-self-test',{method:'POST'});[state.privacy,state.audit]=await Promise.all([api('/governance/privacy'),api('/governance/audit?limit=32')]);state.testingTransfer=false;renderApp();toast(`Secure transfer test ${state.transferTest.status}`)}catch(e){state.testingTransfer=false;renderApp();toast(e.message,'error')}
  }

  document.addEventListener('submit',e=>{
    if(e.target.id==='loginForm'){e.preventDefault();login($('#email').value,$('#password').value);return}
    if(e.target.id==='evidenceForm'){e.preventDefault();ingestEvidence(e.target);return}
    if(e.target.id==='exportForm'){e.preventDefault();exportCustomerData();return}
  });

  document.addEventListener('click',e=>{
    const demo=e.target.closest('[data-demo]');if(demo){login(demo.dataset.demo==='admin'?'superadmin@juristech.com':'user@juristech.com','Finals2026!');return}
    const q=e.target.closest('[data-question]');if(q){submitAsk(q.dataset.question);return}
    const logoutBtn=e.target.closest('[data-action="logout"]');if(logoutBtn){logout();return}
    const view=e.target.closest('[data-view]');if(view){switchView(view.dataset.view);return}
    const solve=e.target.closest('[data-solve]');if(solve){solveGap(solve.dataset.solve);return}
    const back=e.target.closest('[data-action="back-gaps"]');if(back){state.gapDetail=null;renderApp();return}
    const pub=e.target.closest('[data-action="publish-gap"]');if(pub){publishGap();return}
    const test=e.target.closest('[data-action="run-resilience"]');if(test){runResilience();return}
    const twin=e.target.closest('[data-action="run-twin"]');if(twin){runTwin();return}
    const transfer=e.target.closest('[data-action="transfer-test"]');if(transfer){runTransferTest();return}
    const pattern=e.target.closest('[data-pattern-deactivate]');if(pattern){deactivatePattern(pattern.dataset.patternDeactivate);return}
    const feedback=e.target.closest('[data-feedback]');if(feedback){submitFeedback(feedback.dataset.interaction,feedback.dataset.feedback==='helpful');return}
    if(e.target.id==='sendAsk'){submitAsk();return}
  });

  document.addEventListener('change',e=>{if(e.target.classList.contains('shield-toggle'))toggleShield(e.target);if(e.target.id==='compareDomain')changeCompare(e.target.value)});

  bootstrap();
})();
