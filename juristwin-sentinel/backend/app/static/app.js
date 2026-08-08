const JT={token:localStorage.getItem("jt_token"),screen:0,sim:null,approval:null,alert:null,adminMode:"integrations",focus:false,contrast:false,motion:true,zoom:1,selectedOption:"C",memoryRole:"Manager",memoryQuery:"",memoryFilters:{project:"Sentinel",sensitivity:"restricted",version:"v4.2",days:30},filterState:{}};
const SCREEN={login:0,dashboard:1,case:2,conflict:3,twin:4,approval:5,ledger:6,bodyguard:7,memory:8,integrations:9,administration:9};

const stage=document.getElementById("jtStage"),
toastEl=document.getElementById("jtToast"),
modalEl=document.getElementById("jtModal"),
focusBtn=document.getElementById("jtFocusBtn"),
contrastBtn=document.getElementById("jtContrastBtn"),
motionBtn=document.getElementById("jtMotionBtn");

const norm=s=>String(s??"").replace(/\s+/g," ").trim();

async function api(path,opt={}){
    const h={"Content-Type":"application/json",...(opt.headers||{})};

    if(JT.token){
        h.Authorization=`Bearer ${JT.token}`;
    }

    const r=await fetch('/api'+path,{
        ...opt,
        headers:h
    });

    if(!r.ok){
        let m=await r.text();

        try{
            m=JSON.parse(m).detail||m;
        }catch{}

        throw new Error(m);
    }

    return (r.headers.get('content-type')||'').includes('json')
        ? r.json()
        : r;
}

function toast(m,k='info'){
    if(!toastEl)return;

    toastEl.textContent=m;

    toastEl.style.borderColor=
        k==='error'
            ? '#F05454'
            : k==='ok'
                ? '#23C483'
                : '#20C7E8';

    toastEl.style.display='block';

    clearTimeout(toast._t);

    toast._t=setTimeout(()=>{
        toastEl.style.display='none';
    },3300);
}

function leaf(t){
    return [...stage.querySelectorAll('div,span')]
        .find(e=>!e.children.length&&norm(e.textContent)===norm(t));
}

function leaves(t){
    return [...stage.querySelectorAll('div,span')]
        .filter(e=>!e.children.length&&norm(e.textContent)===norm(t));
}

function target(e){
    if(!e)return null;

    let p=e;

    for(let i=0;i<3&&p.parentElement;i++,p=p.parentElement){
        const s=getComputedStyle(p);

        if(
            s.backgroundColor!=='rgba(0, 0, 0, 0)'||
            s.outlineStyle!=='none'||
            s.borderStyle!=='none'
        ){
            return p;
        }
    }

    return e.parentElement||e;
}

function bind(t,fn){
    leaves(t).forEach(e=>{
        const x=target(e);

        if(!x)return;

        x.classList.add('jt-clickable');

        x.addEventListener('click',ev=>{
            ev.stopPropagation();
            fn(ev,x,e);
        });
    });
}

function nav(t,n){
    bind(t,()=>go(n));
}

function modal(h){
    modalEl.innerHTML=`<div class="jt-modal-card">${h}</div>`;
    modalEl.classList.remove('hidden');
}

function closeModal(){
    modalEl.classList.add('hidden');
    modalEl.innerHTML='';
}

window.closeJTModal=closeModal;

function escHtml(v){
    return String(v??'').replace(
        /[&<>"']/g,
        c=>({
            '&':'&amp;',
            '<':'&lt;',
            '>':'&gt;',
            '"':'&quot;',
            "'":'&#039;'
        }[c])
    );
}

function infoModal(title,body,foot=''){
    modal(`
        <h3>${escHtml(title)}</h3>

        <div class="jt-detail-body">
            ${body}
        </div>

        ${foot}

        <div class="jt-modal-actions">
            <button
                class="jt-btn-primary"
                onclick="closeJTModal()"
            >
                Close
            </button>
        </div>
    `);
}

function tinyBadge(text){
    return `
        <span class="jt-modal-badge">
            ${escHtml(text)}
        </span>
    `;
}

/* ============================================================
   ICONS
============================================================ */

function svgIcon(name,size=18,color='#94A3B8'){
    const paths={
        shield:
            '<path d="M12 3l7 3v5c0 4.6-2.7 7.8-7 10-4.3-2.2-7-5.4-7-10V6l7-3z"/>',

        activity:
            '<path d="M3 12h4l2-6 4 12 2-6h6"/>',

        briefcase:
            '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18"/>',

        branch:
            '<circle cx="6" cy="5" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="19" r="2"/><path d="M6 7v10M8 10c6 0 4-4 8-4"/>',

        database:
            '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',

        file:
            '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',

        lock:
            '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',

        grid:
            '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 4v16M4 9h16"/>',

        settings:
            '<circle cx="12" cy="12" r="3"/><path d="M19 13.5l2 1.2-2 3.4-2.1-1a8 8 0 0 1-2.3 1.3L14.4 21h-4.8l-.2-2.6a8 8 0 0 1-2.3-1.3l-2.1 1-2-3.4 2-1.2a8 8 0 0 1 0-3L3 9.3l2-3.4 2.1 1a8 8 0 0 1 2.3-1.3L9.6 3h4.8l.2 2.6a8 8 0 0 1 2.3 1.3l2.1-1 2 3.4-2 1.2a8 8 0 0 1 0 3z"/>',

        search:
            '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',

        play:
            '<path d="M8 5l11 7-11 7z"/>',

        mail:
            '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',

        users:
            '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 20c.5-4 2.5-6 6-6s5.5 2 6 6M15 15c3 0 5 1.5 6 4"/>',

        clock:
            '<circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/>'
    };

    return `
        <svg
            width="${size}"
            height="${size}"
            viewBox="0 0 24 24"
            fill="none"
            stroke="${color}"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
        >
            ${paths[name]||paths.grid}
        </svg>
    `;
}

function replaceIconForLabel(label,name,color='#94A3B8'){
    const e=leaf(label);

    if(!e||!e.parentElement)return;

    const wrap=e.parentElement.firstElementChild;

    if(wrap&&wrap!==e){
        wrap.innerHTML=svgIcon(name,16,color);

        wrap.style.display='flex';
        wrap.style.alignItems='center';
        wrap.style.justifyContent='center';
    }
}

function enhanceIcons(){
    [
        ['Command Center','activity'],
        ['Case Workspace','briefcase'],
        ['Conflict Intelligence','shield'],
        ['Digital Twin','branch'],
        ['Enterprise Memory','database'],
        ['Decision Ledger','file'],
        ['AI Bodyguard','lock'],
        ['Integrations','grid'],
        ['Administration','settings']
    ].forEach(x=>replaceIconForLabel(x[0],x[1]));

    replaceIconForLabel(
        'Query decisions, logs or entities...',
        'search'
    );

    replaceIconForLabel(
        'Start Guided Demo',
        'play',
        '#20C7E8'
    );

    replaceIconForLabel(
        'Work Email',
        'mail'
    );
}

/* ============================================================
   PRESENTATION / ZOOM
============================================================ */

const zoomInBtn=document.getElementById('jtZoomInBtn');
const zoomOutBtn=document.getElementById('jtZoomOutBtn');
const zoomResetBtn=document.getElementById('jtZoomResetBtn');
const fullBtn=document.getElementById('jtFullBtn');
const zoomLabel=document.getElementById('jtZoomLabel');

function fit(){
    const vw=Math.max(
        320,
        window.innerWidth
    );

    const vh=Math.max(
        320,
        window.innerHeight
    );

    const base=JT.focus
        ? Math.min(
            (vw-28)/1440,
            1.18
        )
        : Math.min(
            vw/1440,
            vh/1024
        );

    const scale=Math.max(
        .35,
        Math.min(
            1.65,
            base*(JT.zoom||1)
        )
    );

    const w=1440*scale;
    const h=1024*scale;

    const overflow=
        w>vw||
        h>vh;

    stage.style.transform=
        `scale(${scale})`;

    stage.style.left=
        overflow
            ? '18px'
            : `${Math.max(0,(vw-w)/2)}px`;

    stage.style.top=
        overflow
            ? '18px'
            : JT.focus
                ? '14px'
                : `${Math.max(0,(vh-h)/2)}px`;

    const viewport=
        document.getElementById('jtViewport');

    if(viewport){
        viewport.style.overflow=
            overflow||JT.focus
                ? 'auto'
                : 'hidden';

        viewport.style.height='100%';
    }

    document.body.classList.toggle(
        'jt-stage-zoomed',
        overflow
    );

    if(zoomLabel){
        zoomLabel.textContent=
            `${Math.round((JT.zoom||1)*100)}%`;
    }
}

function setZoom(v){
    JT.zoom=Math.max(
        .55,
        Math.min(
            1.7,
            v
        )
    );

    fit();

    toast(
        `Canvas zoom ${Math.round(JT.zoom*100)}%.`
    );
}

zoomInBtn?.addEventListener(
    'click',
    ()=>{
        setZoom(
            (JT.zoom||1)+.1
        );
    }
);

zoomOutBtn?.addEventListener(
    'click',
    ()=>{
        setZoom(
            (JT.zoom||1)-.1
        );
    }
);

zoomResetBtn?.addEventListener(
    'click',
    ()=>{
        JT.zoom=1;
        JT.focus=false;

        document.body.classList.remove(
            'jt-focus-mode'
        );

        fit();

        toast(
            'Canvas fitted to screen.',
            'ok'
        );
    }
);

fullBtn?.addEventListener(
    'click',
    async()=>{
        try{
            if(!document.fullscreenElement){
                await document
                    .documentElement
                    .requestFullscreen();
            }else{
                await document.exitFullscreen();
            }

            setTimeout(
                fit,
                150
            );
        }catch(e){
            toast(
                'Fullscreen is not available in this browser.',
                'error'
            );
        }
    }
);

window.addEventListener(
    'resize',
    fit
);

window.addEventListener(
    'wheel',
    e=>{
        if(e.ctrlKey||e.metaKey){
            e.preventDefault();

            setZoom(
                (JT.zoom||1)+
                (
                    e.deltaY<0
                        ? .08
                        : -.08
                )
            );
        }
    },
    {
        passive:false
    }
);

function presentationToggle(kind){
    if(kind==='focus'){
        JT.focus=!JT.focus;

        document.body.classList.toggle(
            'jt-focus-mode',
            JT.focus
        );

        focusBtn?.classList.toggle(
            'active',
            JT.focus
        );

        fit();

        toast(
            JT.focus
                ? 'Focus mode enabled.'
                : 'Fit-to-screen mode restored.'
        );
    }

    if(kind==='contrast'){
        JT.contrast=!JT.contrast;

        document.body.classList.toggle(
            'jt-high-contrast',
            JT.contrast
        );

        contrastBtn?.classList.toggle(
            'active',
            JT.contrast
        );

        toast(
            JT.contrast
                ? 'High-contrast projector mode enabled.'
                : 'Standard contrast restored.'
        );
    }

    if(kind==='motion'){
        JT.motion=!JT.motion;

        document.body.classList.toggle(
            'jt-motion-off',
            !JT.motion
        );

        motionBtn?.classList.toggle(
            'active',
            JT.motion
        );

        document.documentElement.style.setProperty(
            '--jt-motion-state',
            JT.motion
                ? 'running'
                : 'paused'
        );

        toast(
            JT.motion
                ? 'Interface motion enabled.'
                : 'Interface motion paused.'
        );
    }
}

focusBtn?.addEventListener(
    'click',
    ()=>presentationToggle('focus')
);

contrastBtn?.addEventListener(
    'click',
    ()=>presentationToggle('contrast')
);

motionBtn?.addEventListener(
    'click',
    ()=>presentationToggle('motion')
);

/* ============================================================
   UI HELPERS
============================================================ */

function visualCard(label,minW=180,minH=45){
    const e=leaf(label);

    if(!e)return null;

    let p=e;

    while(p&&p!==stage){
        const r=p.getBoundingClientRect();
        const s=getComputedStyle(p);

        if(
            r.width>=minW&&
            r.height>=minH&&
            (parseFloat(s.borderRadius)||0)>=5
        ){
            return p;
        }

        p=p.parentElement;
    }

    return target(e);
}

function bindCard(
    label,
    fn,
    minW=180,
    minH=45
){
    const c=visualCard(
        label,
        minW,
        minH
    );

    if(!c)return;

    c.classList.add(
        'jt-clickable',
        'jt-rich-interactive'
    );

    c.setAttribute(
        'tabindex',
        '0'
    );

    c.setAttribute(
        'role',
        'button'
    );

    c.addEventListener(
        'click',
        e=>{
            e.stopPropagation();
            fn(e,c);
        }
    );

    c.addEventListener(
        'keydown',
        e=>{
            if(
                e.key==='Enter'||
                e.key===' '
            ){
                e.preventDefault();
                c.click();
            }
        }
    );
}

function animateNumber(el,to){
    if(!el)return;

    if(!JT.motion){
        el.textContent=to;
        return;
    }

    const targetNum=Number(to);

    if(!Number.isFinite(targetNum)){
        el.textContent=to;
        return;
    }

    const from=0;
    const duration=650;
    const start=performance.now();

    el.classList.add(
        'jt-kpi-value'
    );

    const tick=now=>{
        const p=Math.min(
            1,
            (now-start)/duration
        );

        const ease=
            1-Math.pow(1-p,3);

        el.textContent=
            Math.round(
                from+
                (targetNum-from)*ease
            ).toLocaleString();

        if(p<1){
            requestAnimationFrame(tick);
        }else{
            el.textContent=
                Number.isInteger(targetNum)
                    ? targetNum.toLocaleString()
                    : String(targetNum);
        }
    };

    requestAnimationFrame(tick);
}

function cardVal(label,v){
    const e=leaf(label);

    if(!e||!e.parentElement)return;

    const xs=[
        ...e.parentElement
            .querySelectorAll('div,span')
    ].filter(
        x=>
            !x.children.length&&
            /^-?\d+(\.\d+)?$/
                .test(norm(x.textContent))
    );

    if(xs.length){
        animateNumber(
            xs[0],
            v
        );
    }
}

/* ============================================================
   RENDER / NAVIGATION
============================================================ */

async function render(n=JT.screen){
    JT.screen=n;

    stage.innerHTML=
        '<div class="jt-loading">Loading governed twin interface…</div>';

    try{
        const r=await fetch(
            `/static/screens/screen${n}.html`,
            {
                cache:'no-store'
            }
        );

        if(!r.ok){
            throw new Error(
                'screen missing'
            );
        }

        stage.innerHTML=
            await r.text();

        enhanceIcons();

        fit();

        wire();

        wireInteractiveExtras();

        if(JT.screen===3){
            initEvidenceGraph();
        }

        makeCardsExplorable();

        await hydrate();

    }catch(e){
        console.error(
            'Screen render failed:',
            e
        );

        stage.innerHTML=`
            <div
                style="
                    padding:40px;
                    color:#F8FAFC
                "
            >
                Interface load failed:
                ${escHtml(e.message)}
            </div>
        `;
    }
}

function go(n){
    if(typeof n==='string'){
        n=SCREEN[n];
    }

    if(
        n!==0&&
        !JT.token
    ){
        n=0;
    }

    render(n);
}

/* ============================================================
   LOGIN
============================================================ */

async function login(){
    try{
        const emailInput=
            stage.querySelector(
                'input[type="email"]'
            );

        const passwordInput=
            stage.querySelector(
                'input[type="password"]'
            );

        const email=
            emailInput?.value||
            'operations@regulatedbank.com';

        const password=
            passwordInput?.value||
            'Finals2026!';

        const d=await api(
            '/auth/login',
            {
                method:'POST',
                body:JSON.stringify({
                    email,
                    password
                })
            }
        );

        JT.token=d.access_token;

        localStorage.setItem(
            'jt_token',
            JT.token
        );

        toast(
            'Security Core authenticated.',
            'ok'
        );

        render(1);

    }catch(e){
        toast(
            'Login failed: '+e.message,
            'error'
        );
    }
}

async function guided(){
    if(!JT.token){
        return login();
    }

    try{
        await api(
            '/demo/reset',
            {
                method:'POST'
            }
        );

        JT.sim=null;
        JT.approval=null;
        JT.alert=null;

        toast(
            'Demo reset: Detect → Explain → Simulate → Approve → Audit → Protect.',
            'ok'
        );

        render(1);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   DASHBOARD
============================================================ */

async function dashboard(){
    const d=
        await api('/dashboard');

    cardVal(
        'Active Cases',
        d.metrics.active_cases
    );

    cardVal(
        'Decision Conflicts',
        d.metrics.decision_conflicts
    );

    cardVal(
        'Customers at Risk',
        d.metrics.customers_at_risk
    );

    cardVal(
        'Protected Decisions',
        d.metrics.protected_decisions
    );

    cardVal(
        'Security Alerts',
        d.metrics.security_alerts
    );

    const g=
        leaf(
            'Good morning, Michelle.'
        );

    if(g){
        g.textContent=
            d.greeting;
    }
}

/* ============================================================
   SYSTEM HEALTH / USER
============================================================ */

async function systemHealth(){
    try{
        const h=
            await api('/system/health');

        infoModal(
            'Sentinel System Health',
            `
                <div class="jt-detail-grid">
                    <div>
                        <span>Status</span>
                        <strong>
                            ${escHtml(h.status)}
                        </strong>
                    </div>

                    <div>
                        <span>Database</span>
                        <strong>
                            ${escHtml(h.database)}
                        </strong>
                    </div>

                    <div>
                        <span>Decision Ledger</span>
                        <strong>
                            ${
                                h.decision_ledger?.ok
                                    ? 'Verified'
                                    : 'Check required'
                            }
                        </strong>
                    </div>

                    <div>
                        <span>Environment</span>
                        <strong>
                            Finalist Demo
                        </strong>
                    </div>
                </div>

                <p class="jt-detail-note">
                    This check comes from the live
                    FastAPI backend.
                </p>
            `
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function profileModal(){
    try{
        const u=
            await api('/auth/me');

        infoModal(
            `${u.name||'Michelle Tan'} — Active Identity`,
            `
                <div class="jt-detail-grid">
                    <div>
                        <span>Signed in as</span>
                        <strong>
                            ${escHtml(u.email)}
                        </strong>
                    </div>

                    <div>
                        <span>Role</span>
                        <strong>
                            ${escHtml(u.role)}
                        </strong>
                    </div>

                    <div>
                        <span>Workspace</span>
                        <strong>
                            JurisTwin Sentinel
                        </strong>
                    </div>

                    <div>
                        <span>Session</span>
                        <strong>
                            Authenticated
                        </strong>
                    </div>
                </div>
            `
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   CASE / CONFLICT INFO
============================================================ */

async function showCaseSummary(){
    try{
        const d=
            await api(
                '/cases/JT-2026-084'
            );

        const c=d.case;

        infoModal(
            `Case ${c.case_ref}`,
            `
                <div class="jt-detail-grid">
                    <div>
                        <span>Customer</span>
                        <strong>
                            ${escHtml(c.customer_name)}
                        </strong>
                    </div>

                    <div>
                        <span>Risk</span>
                        <strong>
                            ${escHtml(c.risk_status)}
                        </strong>
                    </div>

                    <div>
                        <span>Pending</span>
                        <strong>
                            ${escHtml(c.pending_days)} days
                        </strong>
                    </div>

                    <div>
                        <span>Protected</span>
                        <strong>
                            ${
                                c.protected
                                    ? 'Yes'
                                    : 'Not yet'
                            }
                        </strong>
                    </div>
                </div>

                <p class="jt-detail-note">
                    ${
                        escHtml(
                            c.current_blocker||
                            'No active blocker.'
                        )
                    }
                </p>
            `,
            `
                <div class="
                    jt-modal-actions
                    jt-modal-actions-secondary
                ">
                    <button
                        class="jt-btn-ghost"
                        id="openCaseNow"
                    >
                        Open Case Workspace
                    </button>
                </div>
            `
        );

        document.getElementById(
            'openCaseNow'
        ).onclick=()=>{
            closeModal();
            go(2);
        };

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function showConflictSummary(
    ref='CF-INCOME-001'
){
    try{
        const c=
            await api(
                `/conflicts/${ref}`
            );

        infoModal(
            c.name,
            `
                <div class="jt-detail-grid">
                    <div>
                        <span>Severity</span>
                        <strong>
                            ${escHtml(c.severity)}
                        </strong>
                    </div>

                    <div>
                        <span>Affected customers</span>
                        <strong>
                            ${c.affected_customers}
                        </strong>
                    </div>

                    <div>
                        <span>Systems affected</span>
                        <strong>
                            ${c.systems_affected}
                        </strong>
                    </div>

                    <div>
                        <span>Confidence</span>
                        <strong>
                            ${
                                Math.round(
                                    c.confidence*
                                    1000
                                )/10
                            }%
                        </strong>
                    </div>
                </div>

                <h4>Root cause</h4>

                <p>
                    ${escHtml(c.root_cause)}
                </p>

                <h4>
                    Recommended resolution
                </h4>

                <p>
                    ${escHtml(c.recommendation)}
                </p>
            `
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

function evidenceModal(
    name,
    source,
    claim,
    authority=''
){
    infoModal(
        name,
        `
            <div class="jt-detail-grid">
                <div>
                    <span>Source</span>
                    <strong>
                        ${escHtml(source)}
                    </strong>
                </div>

                <div>
                    <span>Authority</span>
                    <strong>
                        ${
                            escHtml(
                                authority||
                                'Monitored'
                            )
                        }
                    </strong>
                </div>
            </div>

            <h4>
                Observed evidence
            </h4>

            <p>
                ${escHtml(claim)}
            </p>
        `
    );
}

function documentModal(
    name,
    status,
    detail
){
    infoModal(
        name,
        `
            ${tinyBadge(status)}

            <p>
                ${escHtml(detail)}
            </p>

            <div class="jt-doc-preview">
                <div>
                    GOVERNED DOCUMENT PREVIEW
                </div>

                <strong>
                    ${escHtml(name)}
                </strong>

                <p>
                    Evidence is versioned,
                    access-checked and linked
                    to the active customer
                    decision context.
                </p>
            </div>
        `
    );
}

/* ============================================================
   DIGITAL TWIN
============================================================ */

function optionCard(letter){
    return visualCard(
        `OPTION ${letter}`,
        310,
        180
    );
}

function selectTwinOption(letter){
    JT.selectedOption=letter;

    ['A','B','C'].forEach(
        x=>{
            optionCard(x)
                ?.classList.toggle(
                    'jt-option-selected',
                    x===letter
                );
        }
    );

    const msg={
        A:
            'Take No Action selected — highest delay and complaint risk.',

        B:
            'Update FSD Only selected — partial resolution.',

        C:
            'Align Complete Process selected — recommended governed resolution.'
    }[letter];

    toast(
        msg,
        letter==='C'
            ? 'ok'
            : 'info'
    );
}

function twinMetricEl(
    card,
    label
){
    const l=[
        ...card.querySelectorAll(
            'div,span'
        )
    ].find(
        e=>
            !e.children.length&&
            norm(e.textContent)===label
    );

    if(!l)return null;

    const row=l.parentElement;

    return [
        ...row.querySelectorAll(
            'div,span'
        )
    ].find(
        e=>
            !e.children.length&&
            e!==l&&
            norm(e.textContent)!==label
    )||
    row.lastElementChild;
}

function updateTwinUI(sim){
    if(
        !sim||
        JT.screen!==4
    ){
        return;
    }

    sim.options.forEach(
        o=>{
            const c=
                optionCard(o.key);

            if(!c)return;

            const vals={
                'Predicted Delay':
                    `${o.predicted_delay_days} days`,

                'Complaint Probability':
                    `${o.complaint_probability}%`,

                'Applications Affected':
                    String(
                        o.applications_affected
                    ),

                'Duplicate Requests':
                    String(
                        o.duplicate_requests
                    ),

                'Policy Alignment':
                    `${o.policy_alignment}%`
            };

            Object.entries(vals)
                .forEach(
                    ([k,v])=>{
                        const e=
                            twinMetricEl(c,k);

                        if(e){
                            e.textContent=v;
                        }
                    }
                );

            c.dataset.fit=
                o.decision_fit;

            c.classList.toggle(
                'jt-ai-recommended',
                sim.recommended_option===
                o.key
            );
        }
    );

    stage.querySelector(
        '.jt-twin-live-hud'
    )?.remove();

    const hud=
        document.createElement('div');

    hud.className=
        'jt-twin-live-hud';

    hud.innerHTML=`
        Delay
        <strong>
            ${Math.round(sim.weights.delay*100)}%
        </strong>

        · Complaint
        <strong>
            ${Math.round(sim.weights.complaint*100)}%
        </strong>

        · Alignment
        <strong>
            ${Math.round(sim.weights.alignment*100)}%
        </strong>

        · Recommended
        <strong>
            ${sim.recommended_option}
        </strong>
    `;

    stage.appendChild(hud);
}

function weights(){
    const w=
        JT.sim?.weights||
        {
            delay:.4,
            complaint:.35,
            alignment:.25
        };

    modal(`
        <h3>
            Adjust Live Decision Twin Weights
        </h3>

        <p>
            These sliders change the
            operational emphasis used by
            the backend model.
        </p>

        <div class="jt-weight-slider">
            <div class="jt-weight-slider-head">
                <span>
                    System Delay Priority
                </span>

                <b id="wdv">
                    ${Math.round(w.delay*100)}%
                </b>
            </div>

            <input
                id="wd"
                type="range"
                min="0"
                max="100"
                value="${Math.round(w.delay*100)}"
            >
        </div>

        <div class="jt-weight-slider">
            <div class="jt-weight-slider-head">
                <span>
                    Complaint Risk Priority
                </span>

                <b id="wrv">
                    ${Math.round(w.complaint*100)}%
                </b>
            </div>

            <input
                id="wr"
                type="range"
                min="0"
                max="100"
                value="${Math.round(w.complaint*100)}"
            >
        </div>

        <div class="jt-weight-slider">
            <div class="jt-weight-slider-head">
                <span>
                    Policy Alignment Priority
                </span>

                <b id="wav">
                    ${Math.round(w.alignment*100)}%
                </b>
            </div>

            <input
                id="wa"
                type="range"
                min="0"
                max="100"
                value="${Math.round(w.alignment*100)}"
            >
        </div>

        <div class="jt-weight-total">
            Raw total:
            <strong id="wtot">
                100%
            </strong>

            <br>

            Backend automatically
            normalizes this to 100%.
        </div>

        <div class="jt-modal-actions">
            <button
                class="jt-btn-ghost"
                onclick="closeJTModal()"
            >
                Cancel
            </button>

            <button
                class="jt-btn-primary"
                id="runW"
            >
                Recalculate Twin
            </button>
        </div>
    `);

    const ids=[
        'wd',
        'wr',
        'wa'
    ];

    const refresh=()=>{
        document.getElementById(
            'wdv'
        ).textContent=
            document.getElementById(
                'wd'
            ).value+'%';

        document.getElementById(
            'wrv'
        ).textContent=
            document.getElementById(
                'wr'
            ).value+'%';

        document.getElementById(
            'wav'
        ).textContent=
            document.getElementById(
                'wa'
            ).value+'%';

        document.getElementById(
            'wtot'
        ).textContent=
            ids.reduce(
                (a,id)=>
                    a+
                    Number(
                        document
                            .getElementById(id)
                            .value
                    ),
                0
            )+'%';
    };

    ids.forEach(
        id=>{
            document
                .getElementById(id)
                .addEventListener(
                    'input',
                    refresh
                );
        }
    );

    document.getElementById(
        'runW'
    ).onclick=async()=>{
        try{
            const raw={
                delay:
                    +document
                        .getElementById('wd')
                        .value,

                complaint:
                    +document
                        .getElementById('wr')
                        .value,

                alignment:
                    +document
                        .getElementById('wa')
                        .value
            };

            JT.sim=
                await api(
                    '/simulations/conflict/CF-INCOME-001/run',
                    {
                        method:'POST',
                        body:JSON.stringify({
                            weights:raw
                        })
                    }
                );

            closeModal();

            updateTwinUI(
                JT.sim
            );

            const recommended=
                JT.sim.options.find(
                    x=>
                        x.key===
                        JT.sim.recommended_option
                );

            toast(
                `Twin recomputed. Option ${JT.sim.recommended_option} fit: ${recommended?.decision_fit??'—'}%.`,
                'ok'
            );

        }catch(e){
            toast(
                e.message,
                'error'
            );
        }
    };
}

function compareTwinMetrics(){
    const sim=JT.sim;

    if(!sim){
        toast(
            'Run the Digital Twin first.'
        );

        return;
    }

    const o=
        Object.fromEntries(
            sim.options.map(
                x=>[x.key,x]
            )
        );

    infoModal(
        'Live Decision Twin Comparison',
        `
            <div class="jt-compare-table">

                <div>
                    <b>Metric</b>
                    <b>Option A</b>
                    <b>Option B</b>
                    <b>Option C</b>
                </div>

                <div>
                    <span>
                        Predicted delay
                    </span>

                    <span>
                        ${o.A.predicted_delay_days} d
                    </span>

                    <span>
                        ${o.B.predicted_delay_days} d
                    </span>

                    <strong>
                        ${o.C.predicted_delay_days} d
                    </strong>
                </div>

                <div>
                    <span>
                        Complaint risk
                    </span>

                    <span>
                        ${o.A.complaint_probability}%
                    </span>

                    <span>
                        ${o.B.complaint_probability}%
                    </span>

                    <strong>
                        ${o.C.complaint_probability}%
                    </strong>
                </div>

                <div>
                    <span>
                        Duplicate requests
                    </span>

                    <span>
                        ${o.A.duplicate_requests}
                    </span>

                    <span>
                        ${o.B.duplicate_requests}
                    </span>

                    <strong>
                        ${o.C.duplicate_requests}
                    </strong>
                </div>

                <div>
                    <span>
                        Policy alignment
                    </span>

                    <span>
                        ${o.A.policy_alignment}%
                    </span>

                    <span>
                        ${o.B.policy_alignment}%
                    </span>

                    <strong>
                        ${o.C.policy_alignment}%
                    </strong>
                </div>

                <div>
                    <span>
                        Weighted fit
                    </span>

                    <span>
                        ${o.A.decision_fit}%
                    </span>

                    <span>
                        ${o.B.decision_fit}%
                    </span>

                    <strong>
                        ${o.C.decision_fit}%
                    </strong>
                </div>

            </div>

            <p class="jt-detail-note">
                These values are the
                latest backend simulation.
            </p>
        `
    );
}

/* ============================================================
   APPROVAL
============================================================ */

async function submitApproval(){
    try{
        if(
            JT.selectedOption!=='C'
        ){
            modal(`
                <h3>
                    Option ${JT.selectedOption}
                    is analysis-only
                </h3>

                <p>
                    You can explore every
                    scenario, but only the
                    governed complete-process
                    alignment can be published.
                </p>

                <div class="jt-modal-actions">
                    <button
                        class="jt-btn-ghost"
                        onclick="closeJTModal()"
                    >
                        Keep Comparing
                    </button>

                    <button
                        class="jt-btn-primary"
                        id="switchC"
                    >
                        Select Option C
                    </button>
                </div>
            `);

            document.getElementById(
                'switchC'
            ).onclick=()=>{
                JT.selectedOption='C';
                closeModal();
                submitApproval();
            };

            return;
        }

        if(!JT.sim){
            JT.sim=
                await api(
                    '/simulations/conflict/CF-INCOME-001'
                );
        }

        JT.approval=
            await api(
                `/approvals/simulation/${JT.sim.sim_ref}/submit`,
                {
                    method:'POST',
                    body:JSON.stringify({
                        selected_option:'C',
                        comments:
                            'Complete-process alignment selected from Digital Twin.'
                    })
                }
            );

        toast(
            `${JT.approval.approval_ref} submitted for approval.`,
            'ok'
        );

        render(5);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function pending(){
    if(JT.approval){
        return JT.approval;
    }

    const xs=
        await api('/approvals');

    JT.approval=
        xs.find(
            x=>x.status==='pending'
        )||
        xs.find(
            x=>x.selected_option==='C'
        )||
        null;

    return JT.approval;
}

async function approvalHydrate(){
    const a=
        await pending();

    const banner=
        document.getElementById(
            'approvalPublishedBanner'
        );

    if(a?.status==='approved'){
        if(banner){
            banner.style.display=
                'inline-flex';
        }

        const x=
            leaf(
                'Awaiting Final Authorization'
            );

        if(x){
            x.textContent=
                'Approved — Final authorization recorded';

            x.style.color=
                '#23C483';
        }
    }
}

async function approve(){
    try{
        let a=
            await pending();

        if(!a){
            await submitApproval();
            return;
        }

        const d=
            await api(
                `/approvals/${a.approval_ref}/approve`,
                {
                    method:'POST',
                    body:JSON.stringify({
                        comments:
                            'Final authorization approved in Grand Finals demo.'
                    })
                }
            );

        JT.approval=
            d.approval;

        toast(
            `${d.decision_contract.decision_ref} approved and propagated across ${d.propagation?.cases??27} cases.`,
            'ok'
        );

        render(5);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function requestApprovalChanges(){
    try{
        const a=
            await pending();

        if(!a){
            throw new Error(
                'No pending approval.'
            );
        }

        await api(
            `/approvals/${a.approval_ref}/request-changes`,
            {
                method:'POST',
                body:JSON.stringify({
                    comments:
                        'Compliance requested clarification before final authorization.'
                })
            }
        );

        toast(
            'Change request recorded in the approval trail.',
            'ok'
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function rejectApproval(){
    try{
        const a=
            await pending();

        if(!a){
            throw new Error(
                'No pending approval.'
            );
        }

        await api(
            `/approvals/${a.approval_ref}/reject`,
            {
                method:'POST',
                body:JSON.stringify({
                    comments:
                        'Rejected during governed review.'
                })
            }
        );

        toast(
            'Resolution rejected.',
            'error'
        );

        render(4);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   ENTERPRISE MEMORY
============================================================ */

const MEM_CYCLES={
    'Source: All':[
        {
            label:'Source: All',
            k:'source',
            v:null
        },
        {
            label:'Source: Outlook',
            k:'source',
            v:'Outlook'
        },
        {
            label:'Source: Teams',
            k:'source',
            v:'Teams'
        },
        {
            label:'Source: QA',
            k:'source',
            v:'QA'
        },
        {
            label:'Source: SharePoint',
            k:'source',
            v:'SharePoint'
        }
    ],

    'Customer: Any':[
        {
            label:'Customer: Any',
            k:'customer',
            v:null
        },
        {
            label:'Customer: Aina',
            k:'customer',
            v:'Aina Rahman'
        },
        {
            label:'Customer: JT-2026-091',
            k:'customer',
            v:'JT-2026-091'
        },
        {
            label:'Customer: System Audit',
            k:'customer',
            v:'System Audit'
        }
    ],

    'Project: Sentinel':[
        {
            label:'Project: Sentinel',
            k:'project',
            v:'Sentinel'
        },
        {
            label:'Project: Credit Ops',
            k:'project',
            v:'Credit Operations'
        },
        {
            label:'Project: Compliance Ops',
            k:'project',
            v:'Compliance Operations'
        },
        {
            label:'Project: Governance Core',
            k:'project',
            v:'Governance Core'
        },
        {
            label:'Project: All',
            k:'project',
            v:null
        }
    ],

    'Decision Tiers':[
        {
            label:'Decision Tiers',
            k:'decision_tier',
            v:null
        },
        {
            label:'Tier: 3',
            k:'decision_tier',
            v:3
        },
        {
            label:'Tier: 2',
            k:'decision_tier',
            v:2
        },
        {
            label:'Tier: 1',
            k:'decision_tier',
            v:1
        }
    ],

    'Authority Level':[
        {
            label:'Authority Level',
            k:'authority_level',
            v:null
        },
        {
            label:'Authority ≥ 5',
            k:'authority_level',
            v:5
        },
        {
            label:'Authority ≥ 3',
            k:'authority_level',
            v:3
        }
    ],

    'Sensitivity: Restricted':[
        {
            label:'Sensitivity: Restricted',
            k:'sensitivity',
            v:'restricted'
        },
        {
            label:'Sensitivity: Confidential',
            k:'sensitivity',
            v:'confidential'
        },
        {
            label:'Sensitivity: Internal',
            k:'sensitivity',
            v:'internal'
        },
        {
            label:'Sensitivity: All',
            k:'sensitivity',
            v:null
        }
    ],

    'Compliance Status':[
        {
            label:'Compliance Status',
            k:'status',
            v:null
        },
        {
            label:'Status: Active',
            k:'status',
            v:'active'
        },
        {
            label:'Status: Superseded',
            k:'status',
            v:'superseded'
        }
    ],

    'v4.2 Active':[
        {
            label:'Version: All',
            k:'version',
            v:null
        },
        {
            label:'Version: v4.2',
            k:'version',
            v:'v4.2'
        },
        {
            label:'Version: v4.1',
            k:'version',
            v:'v4.1'
        },
        {
            label:'Version: v3.0',
            k:'version',
            v:'v3.0'
        }
    ],

    'Date Range: 30D':[
        {
            label:'Date: 30D',
            k:'days',
            v:30
        },
        {
            label:'Date: 7D',
            k:'days',
            v:7
        },
        {
            label:'Date: 90D',
            k:'days',
            v:90
        },
        {
            label:'Date: All',
            k:'days',
            v:null
        }
    ]
};

const MEM_INDEX={};

function previewRoleKey(){
    return {
        Manager:'manager',
        Officer:'officer',
        Intern:'intern'
    }[JT.memoryRole]||'manager';
}

async function refreshMemoryResults(){
    const payload={
        query:
            JT.memoryQuery||'',

        limit:6,

        filters:
            JT.memoryFilters||{},

        preview_role:
            previewRoleKey()
    };

    const r=
        await api(
            '/memory/search',
            {
                method:'POST',
                body:JSON.stringify(payload)
            }
        );

    renderMemoryResults(r);

    return r;
}

function renderMemoryResults(r){
    if(JT.screen!==8)return;

    stage.querySelector(
        '.jt-memory-live'
    )?.remove();

    const box=
        document.createElement('div');

    box.className=
        'jt-live-overlay jt-memory-live';

    const filters=
        Object.entries(
            r.filters||{}
        )
        .filter(([,v])=>v!=null)
        .map(
            ([k,v])=>
                `${k}: ${v}`
        )
        .join(' · ');

    box.innerHTML=`
        <div class="jt-memory-summary">
            <span>
                ${r.count}
                live evidence matches
                · preview role:
                <b>
                    ${escHtml(r.role)}
                </b>
            </span>

            <span>
                ${
                    escHtml(
                        filters||
                        'No filters'
                    )
                }
            </span>
        </div>

        <div class="jt-memory-result-grid">

            ${
                r.results.length

                ? r.results
                    .slice(0,4)
                    .map(
                        x=>`
                            <div
                                class="jt-memory-result"
                                data-ref="${escHtml(x.evidence_ref)}"
                            >
                                <div class="jt-memory-result-head">
                                    <h4>
                                        ${escHtml(x.title)}
                                    </h4>

                                    <span class="jt-memory-score">
                                        ${Math.round((x.score||0)*100)}%
                                        match
                                    </span>
                                </div>

                                <p>
                                    ${
                                        escHtml(
                                            (x.body||'')
                                            .slice(0,190)
                                        )
                                    }
                                </p>

                                <div class="jt-memory-meta">
                                    <span>
                                        ${escHtml(x.source)}
                                    </span>

                                    <span>
                                        ${escHtml(x.sensitivity)}
                                    </span>

                                    <span>
                                        ${escHtml(x.version||'live')}
                                    </span>

                                    <span>
                                        Authority
                                        ${x.authority_level}
                                    </span>

                                    <span>
                                        ${escHtml(x.status)}
                                    </span>
                                </div>
                            </div>
                        `
                    )
                    .join('')

                : `
                    <div class="jt-memory-empty">
                        No evidence matches this
                        filter combination.
                    </div>
                `
            }

        </div>
    `;

    stage.appendChild(box);

    box.querySelectorAll(
        '.jt-memory-result'
    ).forEach(
        el=>{
            el.onclick=()=>{
                const result=
                    r.results.find(
                        x=>
                            x.evidence_ref===
                            el.dataset.ref
                    );

                openLiveEvidence(result);
            };
        }
    );
}

function openLiveEvidence(x){
    if(!x)return;

    modal(`
        <h3>
            ${escHtml(x.title)}
        </h3>

        ${tinyBadge(x.sensitivity)}

        <div class="jt-detail-grid">
            <div>
                <span>Source</span>
                <strong>
                    ${escHtml(x.source)}
                </strong>
            </div>

            <div>
                <span>Authority</span>
                <strong>
                    ${
                        escHtml(
                            x.authority||
                            'Monitored'
                        )
                    }
                </strong>
            </div>

            <div>
                <span>Version</span>
                <strong>
                    ${escHtml(x.version||'live')}
                </strong>
            </div>

            <div>
                <span>Status</span>
                <strong>
                    ${escHtml(x.status)}
                </strong>
            </div>
        </div>

        <p>
            ${escHtml(x.body)}
        </p>

        <div class="jt-modal-actions">
            <button
                class="jt-btn-ghost"
                onclick="closeJTModal()"
            >
                Close
            </button>

            <button
                class="jt-btn-primary"
                id="memDownload"
            >
                Run DLP Download Check
            </button>
        </div>
    `);

    document.getElementById(
        'memDownload'
    ).onclick=async()=>{
        try{
            const d=
                await api(
                    `/memory/${x.evidence_ref}/download`
                );

            toast(
                `DLP check passed for ${d.evidence.title}.`,
                'ok'
            );

        }catch(e){
            toast(
                e.message,
                'error'
            );
        }
    };
}

async function memoryHydrate(){
    await refreshMemoryResults();
}

function memorySearch(){
    modal(`
        <h3>
            Search Secure Enterprise Memory
        </h3>

        <p>
            Search the live role-aware
            evidence store.
        </p>

        <label>
            Query
        </label>

        <input
            id="mq"
            value="${escHtml(JT.memoryQuery||'')}"
        >

        <div class="jt-modal-actions">
            <button
                class="jt-btn-ghost"
                onclick="closeJTModal()"
            >
                Cancel
            </button>

            <button
                class="jt-btn-primary"
                id="mrun"
            >
                Search & Refresh
            </button>
        </div>
    `);

    document.getElementById(
        'mrun'
    ).onclick=async()=>{
        JT.memoryQuery=
            document.getElementById(
                'mq'
            ).value;

        closeModal();

        try{
            const r=
                await refreshMemoryResults();

            toast(
                `${r.count} evidence matches displayed.`,
                'ok'
            );

        }catch(e){
            toast(
                e.message,
                'error'
            );
        }
    };
}

async function toggleFilter(label){
    const cycle=
        MEM_CYCLES[label];

    if(!cycle)return;

    const i=
        (MEM_INDEX[label]??0)+1;

    MEM_INDEX[label]=
        i%cycle.length;

    const next=
        cycle[
            MEM_INDEX[label]
        ];

    if(next.v==null){
        delete JT.memoryFilters[next.k];
    }else{
        JT.memoryFilters[next.k]=next.v;
    }

    try{
        await refreshMemoryResults();

        toast(
            `${next.label} applied.`,
            'ok'
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function switchMemoryRole(role){
    JT.memoryRole=role;

    [
        'Manager View (Full Access)',
        'Officer View (Assigned Cases Only)',
        'Intern View (Redacted Tiers)'
    ].forEach(
        t=>
            visualCard(t,270,120)
                ?.classList.remove(
                    'jt-role-selected'
                )
    );

    const label=
        role==='Manager'
            ? 'Manager View (Full Access)'
            : role==='Officer'
                ? 'Officer View (Assigned Cases Only)'
                : 'Intern View (Redacted Tiers)';

    visualCard(
        label,
        270,
        120
    )?.classList.add(
        'jt-role-selected'
    );

    try{
        await refreshMemoryResults();

        toast(
            `${role} access preview applied.`,
            'ok'
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   LEDGER
============================================================ */

async function ledgerHydrate(){
    const ds=
        await api(
            '/ledger/decisions'
        );

    const d=
        ds.find(
            x=>
                x.decision_ref===
                'JT-084'
        );

    if(!d){
        renderLedgerEmpty();
        return;
    }

    const live=
        await api(
            '/ledger/decisions/JT-084'
        );

    renderLedgerLive(live);
}

function renderLedgerEmpty(){
    stage.querySelector(
        '.jt-ledger-live'
    )?.remove();

    const box=
        document.createElement('div');

    box.className=
        'jt-live-overlay jt-ledger-live';

    box.innerHTML=`
        <div class="jt-ledger-contract">
            <div class="jt-ledger-title">
                <h3>
                    No published JT-084
                    decision yet
                </h3>
            </div>

            <p class="jt-ledger-rule">
                Run the Decision Digital Twin
                and approve Option C first.
            </p>

            <button
                class="jt-small-btn primary"
                id="ledgerGoTwin"
            >
                Open Digital Twin
            </button>
        </div>
    `;

    stage.appendChild(box);

    document.getElementById(
        'ledgerGoTwin'
    ).onclick=()=>{
        go(4);
    };
}

function renderLedgerLive(data){
    stage.querySelector(
        '.jt-ledger-live'
    )?.remove();

    const d=data.decision;
    const chain=data.chain;

    const box=
        document.createElement('div');

    box.className=
        'jt-live-overlay jt-ledger-live';

    box.innerHTML=`
        <div class="jt-ledger-head">

            <div class="
                jt-ledger-contract
                active
            ">

                <div class="jt-ledger-title">
                    <h3>
                        RECORD:
                        ${escHtml(d.decision_ref)}
                        ·
                        ${escHtml(d.version)}
                    </h3>

                    <span class="jt-modal-badge">
                        ${escHtml(d.status)}
                    </span>
                </div>

                <div class="jt-ledger-rule">
                    “${escHtml(d.approved_rule)}”
                </div>

                <div class="jt-ledger-meta">

                    <div>
                        Approved by
                        <strong>
                            ${escHtml(d.approved_by)}
                        </strong>
                    </div>

                    <div>
                        Supersedes
                        <strong>
                            ${
                                escHtml(
                                    d.supersedes||
                                    '—'
                                )
                            }
                        </strong>
                    </div>

                    <div>
                        Chain
                        <strong>
                            ${
                                chain.ok
                                    ? 'VERIFIED'
                                    : 'CHECK REQUIRED'
                            }

                            · ${chain.entries}
                            entries
                        </strong>
                    </div>

                </div>

                <div class="jt-ledger-toolbar">

                    <button
                        class="jt-small-btn primary"
                        id="ledgerRefresh"
                    >
                        Refresh Latest
                    </button>

                    <button
                        class="jt-small-btn"
                        id="ledgerVerify"
                    >
                        Verify Hash Chain
                    </button>

                    <button
                        class="jt-small-btn"
                        id="ledgerExport"
                    >
                        Export CSV
                    </button>

                </div>
            </div>

            <div class="jt-ledger-versions">

                <div class="jt-ledger-title">
                    <h3>
                        Version History
                    </h3>
                </div>

                <div class="jt-ledger-version-list">

                    ${
                        data.versions
                        .map(
                            v=>`
                                <div
                                    class="
                                        jt-ledger-version
                                        ${
                                            v.status==='active'
                                                ? 'active'
                                                : ''
                                        }
                                    "
                                    data-version="${escHtml(v.version)}"
                                >
                                    <strong>
                                        ${escHtml(v.version)}
                                        ·
                                        ${
                                            escHtml(
                                                v.change_type
                                                .replaceAll('_',' ')
                                            )
                                        }
                                    </strong>

                                    <span>
                                        ${
                                            escHtml(
                                                v.rule_text
                                                .slice(0,92)
                                            )
                                        }
                                    </span>

                                    <span>
                                        ${escHtml(v.actor)}
                                    </span>
                                </div>
                            `
                        )
                        .join('')
                    }

                </div>
            </div>
        </div>

        <div class="jt-ledger-body">

            <div class="jt-ledger-versions">
                <div class="jt-ledger-title">
                    <h3>
                        Governance State
                    </h3>
                </div>

                <div class="jt-mini-list">

                    <div>
                        <b>Retention Lock</b>
                        <span>
                            ${
                                data.retention_lock.enabled
                                    ? 'ENABLED'
                                    : 'DISABLED'
                            }
                        </span>
                    </div>

                    <div>
                        <b>Applications</b>
                        <span>
                            ${d.affected.applications||0}
                        </span>
                    </div>

                    <div>
                        <b>QA Tests</b>
                        <span>
                            ${d.affected.qa_tests||0}
                        </span>
                    </div>

                    <div>
                        <b>Officers</b>
                        <span>
                            ${d.affected.officers_notified||0}
                        </span>
                    </div>

                </div>
            </div>

            <div class="jt-ledger-audit">

                <div class="jt-ledger-title">
                    <h3>
                        Live Immutable Audit Trail
                    </h3>

                    <span>
                        ${data.audit_trail.length}
                        events
                    </span>
                </div>

                <div class="jt-ledger-audit-list">

                    ${
                        data.audit_trail
                        .slice()
                        .reverse()
                        .map(
                            e=>`
                                <div
                                    class="jt-ledger-row"
                                    data-tx="${escHtml(e.txid)}"
                                >
                                    <b>
                                        ${escHtml(e.txid)}
                                    </b>

                                    <span>
                                        ${
                                            escHtml(
                                                e.action
                                                .replaceAll('_',' ')
                                            )
                                        }
                                    </span>

                                    <span>
                                        ${escHtml(e.actor)}
                                    </span>

                                    <span>
                                        ${
                                            new Date(
                                                e.created_at
                                            )
                                            .toLocaleTimeString()
                                        }
                                    </span>
                                </div>
                            `
                        )
                        .join('')
                    }

                </div>
            </div>
        </div>
    `;

    stage.appendChild(box);

    document.getElementById(
        'ledgerRefresh'
    ).onclick=
        ledgerHydrate;

    document.getElementById(
        'ledgerVerify'
    ).onclick=
        showLedgerIntegrity;

    document.getElementById(
        'ledgerExport'
    ).onclick=
        exportLedger;

    box.querySelectorAll(
        '.jt-ledger-version'
    ).forEach(
        el=>{
            el.onclick=()=>{
                const v=
                    data.versions.find(
                        x=>
                            x.version===
                            el.dataset.version
                    );

                infoModal(
                    `${v.version} — ${v.change_type.replaceAll('_',' ')}`,
                    `
                        <p>
                            ${escHtml(v.rule_text)}
                        </p>

                        <div class="jt-detail-grid">
                            <div>
                                <span>Actor</span>
                                <strong>
                                    ${escHtml(v.actor)}
                                </strong>
                            </div>

                            <div>
                                <span>Status</span>
                                <strong>
                                    ${escHtml(v.status)}
                                </strong>
                            </div>
                        </div>
                    `
                );
            };
        }
    );

    box.querySelectorAll(
        '.jt-ledger-row'
    ).forEach(
        el=>{
            el.onclick=()=>{
                const e=
                    data.audit_trail.find(
                        x=>
                            x.txid===
                            el.dataset.tx
                    );

                infoModal(
                    e.action
                    .replaceAll('_',' '),
                    `
                        <div class="jt-detail-grid">
                            <div>
                                <span>TXID</span>
                                <strong>
                                    ${escHtml(e.txid)}
                                </strong>
                            </div>

                            <div>
                                <span>Actor</span>
                                <strong>
                                    ${escHtml(e.actor)}
                                </strong>
                            </div>
                        </div>

                        <pre
                            style="
                                white-space:pre-wrap;
                                color:#B9C7D8;
                                background:#07111F;
                                padding:12px;
                                border-radius:8px
                            "
                        >${escHtml(JSON.stringify(e.payload,null,2))}</pre>
                    `
                );
            };
        }
    );
}

async function showLedgerIntegrity(){
    try{
        const v=
            await api(
                '/ledger/verify'
            );

        infoModal(
            'Immutable Ledger Integrity',
            `
                <div class="
                    jt-ledger-verify
                    ${
                        v.ok
                            ? 'ok'
                            : 'bad'
                    }
                ">

                    <strong>
                        ${
                            v.ok
                                ? '✓ HASH CHAIN VERIFIED'
                                : '! INTEGRITY CHECK FAILED'
                        }
                    </strong>

                    <p>
                        ${
                            v.ok
                                ? 'Every governed ledger record links correctly to the previous SHA-256 hash.'
                                : 'One or more ledger links require investigation.'
                        }
                    </p>

                </div>
            `
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function compareVersions(){
    try{
        const d=
            await api(
                '/ledger/decisions/JT-084'
            );

        const rows=
            d.versions
            .map(
                v=>`
                    <div class="${
                        v.status==='active'
                            ? 'active'
                            : ''
                    }">

                        <span>
                            ${escHtml(v.version)}
                            —
                            ${
                                escHtml(
                                    v.change_type
                                    .replaceAll('_',' ')
                                )
                            }
                        </span>

                        <strong>
                            ${escHtml(v.rule_text)}
                        </strong>

                        <p>
                            ${escHtml(v.actor)}
                        </p>

                    </div>
                `
            )
            .join('');

        infoModal(
            'Live Decision Version Comparison',
            `
                <div class="jt-version-compare">
                    ${rows}
                </div>
            `
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function exportLedger(){
    try{
        const r=
            await fetch(
                '/api/ledger/export.csv',
                {
                    headers:{
                        Authorization:
                            `Bearer ${JT.token}`
                    }
                }
            );

        if(!r.ok){
            throw new Error(
                await r.text()
            );
        }

        const b=
            await r.blob();

        const u=
            URL.createObjectURL(b);

        const a=
            document.createElement('a');

        a.href=u;

        a.download=
            'juristwin_decision_ledger.csv';

        a.click();

        URL.revokeObjectURL(u);

        toast(
            'Audit report exported.',
            'ok'
        );

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   BODYGUARD
============================================================ */

function setText(id,value){
    const e=
        document.getElementById(id);

    if(e&&value!=null){
        e.textContent=value;
    }
}

function ensureAlertStatus(xs){
    return xs.find(
        x=>
            [
                'open',
                'reviewed',
                'escalated',
                'access_revoked',
                'authorized_override'
            ].includes(x.status)
    )||
    xs[0];
}

async function ensureAlert(){
    const xs=
        await api(
            '/bodyguard/alerts'
        );

    let a=
        ensureAlertStatus(xs);

    if(!a){
        a=
            await api(
                '/bodyguard/simulate-attack',
                {
                    method:'POST'
                }
            );
    }

    JT.alert=a;

    return a;
}

async function bodyguardHydrate(){
    const s=
        await api(
            '/demo/status'
        );

    if(!s.decision_published){
        toast(
            'Publish JT-084 first. Bodyguard protects approved decisions after publication.'
        );

        return;
    }

    const dash=
        await api('/dashboard');

    cardVal(
        'Protected decisions',
        dash.metrics.protected_decisions
    );

    cardVal(
        'High-risk incidents',
        dash.metrics.security_alerts
    );

    const a=
        await ensureAlert();

    setText(
        'bgTriggerUser',
        `User ${a.user_ref}`
    );

    setText(
        'bgDocument',
        a.document
    );

    setText(
        'bgDecision',
        `Decision ${a.conflict_decision_ref}`
    );

    const banner=
        document.getElementById(
            'bodyguardRestoreBanner'
        );

    if(banner){
        banner.style.display=
            a.status==='restored'
                ? 'flex'
                : 'none';
    }
}

async function reviewBodyguardActivity(){
    try{
        const a=
            await ensureAlert();

        JT.alert=
            await api(
                `/bodyguard/alerts/${a.alert_ref}/review`,
                {
                    method:'POST'
                }
            );

        const rows=
            JT.alert.timeline
            .map(
                x=>`
                    <div
                        style="
                            display:flex;
                            justify-content:space-between;
                            gap:12px;
                            padding:8px 0;
                            border-bottom:
                                1px solid #172C45
                        "
                    >
                        <div>
                            <b>
                                ${escHtml(x.action)}
                            </b>

                            ${
                                x.detail
                                    ? `
                                        <div
                                            style="
                                                color:#94A3B8;
                                                font-size:12px
                                            "
                                        >
                                            ${escHtml(x.detail)}
                                        </div>
                                    `
                                    : ''
                            }
                        </div>

                        <span
                            style="
                                color:#94A3B8
                            "
                        >
                            ${escHtml(x.time||x.status)}
                        </span>
                    </div>
                `
            )
            .join('');

        modal(`
            <h3>
                Reviewed Activity Trail
            </h3>

            <p>
                Incident is now marked
                reviewed in the backend and
                ledger.
            </p>

            ${rows}

            <div class="jt-modal-actions">
                <button
                    class="jt-btn-primary"
                    onclick="closeJTModal()"
                >
                    Close
                </button>
            </div>
        `);

        if(JT.screen===7){
            bodyguardHydrate();
        }

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function requestBodyguardExplanation(){
    try{
        const a=
            await ensureAlert();

        const x=
            await api(
                `/bodyguard/alerts/${a.alert_ref}/explain`,
                {
                    method:'POST'
                }
            );

        modal(`
            <h3>
                Sentinel White-Box Explanation
            </h3>

            <p>
                ${escHtml(x.summary)}
            </p>

            ${
                x.reasons
                .map(
                    r=>`
                        <div
                            style="
                                margin:8px 0;
                                padding:10px 12px;
                                background:#12243A;
                                border-radius:6px
                            "
                        >
                            • ${escHtml(r)}
                        </div>
                    `
                )
                .join('')
            }

            <h4>
                Current protected decision
            </h4>

            <p>
                ${escHtml(x.decision||'—')}

                <b>
                    ${escHtml(x.decision_version||'')}
                </b>
            </p>

            <h4>
                Recommended actions
            </h4>

            <div class="jt-mini-list">
                ${
                    x.recommended_actions
                    .map(
                        r=>`
                            <div>
                                <span>
                                    ${escHtml(r)}
                                </span>
                            </div>
                        `
                    )
                    .join('')
                }
            </div>

            <div class="jt-modal-actions">
                <button
                    class="jt-btn-primary"
                    onclick="closeJTModal()"
                >
                    Close
                </button>
            </div>
        `);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function revokeBodyguardAccess(){
    try{
        const a=
            await ensureAlert();

        modal(`
            <h3>
                Revoke ${escHtml(a.user_ref)} Access?
            </h3>

            <p>
                This disables the seeded QA
                account in the backend and
                records the action in the ledger.
            </p>

            <div class="jt-modal-actions">

                <button
                    class="jt-btn-ghost"
                    onclick="closeJTModal()"
                >
                    Cancel
                </button>

                <button
                    class="jt-btn-primary"
                    id="confirmRevoke"
                >
                    Revoke Access
                </button>

            </div>
        `);

        document.getElementById(
            'confirmRevoke'
        ).onclick=async()=>{
            try{
                const r=
                    await api(
                        `/bodyguard/alerts/${a.alert_ref}/revoke-access`,
                        {
                            method:'POST'
                        }
                    );

                JT.alert=
                    r.alert||r;

                closeModal();

                toast(
                    `${a.user_ref} account disabled. Ledger updated.`,
                    'ok'
                );

                render(7);

            }catch(e){
                toast(
                    e.message,
                    'error'
                );
            }
        };

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function escalateBodyguard(){
    try{
        const a=
            await ensureAlert();

        JT.alert=
            await api(
                `/bodyguard/alerts/${a.alert_ref}/escalate`,
                {
                    method:'POST'
                }
            );

        toast(
            'Incident escalated to Compliance Manager and written to the ledger.',
            'ok'
        );

        render(7);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function authorizeBodyguardOverwrite(){
    try{
        const a=
            await ensureAlert();

        modal(`
            <h3>
                Authorise the Modified Policy?
            </h3>

            <p>
                This creates a real new
                Decision Contract version and
                re-evaluates affected cases.
            </p>

            <label>
                Override justification
            </label>

            <textarea id="overrideReason">Compliance exception authorised after manual review.</textarea>

            <div class="jt-modal-actions">

                <button
                    class="jt-btn-ghost"
                    onclick="closeJTModal()"
                >
                    Cancel
                </button>

                <button
                    class="jt-btn-primary"
                    id="confirmOverride"
                >
                    Authorise & Version
                </button>

            </div>
        `);

        document.getElementById(
            'confirmOverride'
        ).onclick=async()=>{
            try{
                const r=
                    await api(
                        `/bodyguard/alerts/${a.alert_ref}/authorize-overwrite`,
                        {
                            method:'POST',
                            body:JSON.stringify({
                                comments:
                                    document.getElementById(
                                        'overrideReason'
                                    ).value
                            })
                        }
                    );

                JT.alert=
                    r.alert;

                closeModal();

                toast(
                    `Authorised overwrite published as ${r.decision_version}. ${r.affected_cases} cases re-evaluated.`,
                    'ok'
                );

                render(7);

            }catch(e){
                toast(
                    e.message,
                    'error'
                );
            }
        };

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function restore(){
    try{
        const a=
            await ensureAlert();

        JT.alert=
            await api(
                `/bodyguard/alerts/${a.alert_ref}/restore`,
                {
                    method:'POST'
                }
            );

        toast(
            'Approved rule restored as a new decision version.',
            'ok'
        );

        render(7);

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   RBAC + SHIELDS
============================================================ */

const ROLE_MAP={
    Manager:'manager',
    Officer:'officer',
    Intern:'intern',
    'Compliance Auditor':'compliance_manager',
    'Product Owner':'product_owner',
    'QA Analyst':'qa_analyst'
};

const SHIELD_MAP={
    'Data Sensitivity Masking':
        'data_masking',

    'Active DLP Protection':
        'dlp',

    '7-Year Ledger Retention':
        'ledger_retention',

    'OOH Modification Guard':
        'ooh_guard'
};

async function roleInfo(
    role,
    desc=''
){
    try{
        const cfg=
            await api(
                '/system/config'
            );

        const key=
            ROLE_MAP[role]||
            role;

        const p=
            cfg.rbac.find(
                x=>x.role===key
            );

        if(!p){
            infoModal(
                `${role} — RBAC`,
                `<p>${escHtml(desc)}</p>`
            );

            return;
        }

        modal(`
            <h3>
                ${escHtml(role)}
                — Live RBAC Policy
            </h3>

            <p>
                ${escHtml(p.description)}
            </p>

            <label>
                Maximum sensitivity tier
                (0 Public → 3 Restricted)
            </label>

            <input
                id="rpSens"
                type="number"
                min="0"
                max="3"
                value="${p.max_sensitivity}"
            >

            <div class="jt-mini-list">

                <label>
                    <input
                        id="rpEnabled"
                        type="checkbox"
                        ${p.enabled?'checked':''}
                    >
                    Role enabled
                </label>

                <label>
                    <input
                        id="rpTwin"
                        type="checkbox"
                        ${p.can_modify_twin?'checked':''}
                    >
                    Modify Digital Twin
                </label>

                <label>
                    <input
                        id="rpOverride"
                        type="checkbox"
                        ${p.can_override?'checked':''}
                    >
                    Authorise overrides
                </label>

                <label>
                    <input
                        id="rpExport"
                        type="checkbox"
                        ${p.can_export_ledger?'checked':''}
                    >
                    Export Decision Ledger
                </label>

                <label>
                    <input
                        id="rpReview"
                        type="checkbox"
                        ${p.can_review_bodyguard?'checked':''}
                    >
                    Review Bodyguard incidents
                </label>

            </div>

            <div class="jt-modal-actions">

                <button
                    class="jt-btn-ghost"
                    onclick="closeJTModal()"
                >
                    Cancel
                </button>

                <button
                    class="jt-btn-primary"
                    id="saveRole"
                >
                    Save RBAC Policy
                </button>

            </div>
        `);

        document.getElementById(
            'saveRole'
        ).onclick=async()=>{
            try{
                await api(
                    `/system/roles/${key}`,
                    {
                        method:'PATCH',
                        body:JSON.stringify({
                            enabled:
                                document
                                    .getElementById('rpEnabled')
                                    .checked,

                            max_sensitivity:
                                +document
                                    .getElementById('rpSens')
                                    .value,

                            can_modify_twin:
                                document
                                    .getElementById('rpTwin')
                                    .checked,

                            can_override:
                                document
                                    .getElementById('rpOverride')
                                    .checked,

                            can_export_ledger:
                                document
                                    .getElementById('rpExport')
                                    .checked,

                            can_review_bodyguard:
                                document
                                    .getElementById('rpReview')
                                    .checked
                        })
                    }
                );

                closeModal();

                toast(
                    `${role} RBAC policy persisted and ledgered.`,
                    'ok'
                );

                adminHydrate();

            }catch(e){
                toast(
                    e.message,
                    'error'
                );
            }
        };

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

async function toggleShield(label){
    try{
        const cfg=
            await api(
                '/system/config'
            );

        const key=
            SHIELD_MAP[label];

        const s=
            cfg.shields.find(
                x=>x.key===key
            );

        if(!s){
            throw new Error(
                'Shield not found'
            );
        }

        const updated=
            await api(
                `/system/shields/${key}`,
                {
                    method:'PATCH',
                    body:JSON.stringify({
                        enabled:
                            !s.enabled
                    })
                }
            );

        toast(
            `${label} ${updated.enabled?'enabled':'disabled'} in backend policy state.`,
            'ok'
        );

        adminHydrate();

    }catch(e){
        toast(
            e.message,
            'error'
        );
    }
}

/* ============================================================
   INTEGRATIONS
============================================================ */

async function adminHydrate(){
    const [
        ints,
        cfg
    ]=
        await Promise.all([
            api('/integrations'),
            api('/system/config')
        ]);

    renderIntegrations(ints);

    applyAdminState(cfg);
}

function renderIntegrations(ints){
    stage.querySelector(
        '.jt-integration-live'
    )?.remove();

    const box=
        document.createElement('div');

    box.className=
        'jt-live-overlay jt-integration-live';

    box.innerHTML=`
        <div class="jt-memory-summary">
            <span>
                Live Enterprise Core Integrations
            </span>

            <span>
                Click any connector to manage it
            </span>
        </div>

        <div class="jt-connector-grid">

            ${
                ints.map(
                    i=>{
                        const d=
                            i.details||{};

                        const err=
                            Number(
                                d.errors||0
                            );

                        return `
                            <div
                                class="jt-connector-card"
                                data-key="${escHtml(i.key)}"
                            >
                                <div class="jt-connector-head">
                                    <strong>
                                        ${escHtml(i.name)}
                                    </strong>

                                    <span
                                        class="
                                            jt-connector-status
                                            ${i.status}
                                        "
                                    >
                                        ${
                                            escHtml(
                                                i.status.toUpperCase()
                                            )
                                        }
                                    </span>
                                </div>

                                <div class="jt-connector-body">

                                    <span>
                                        Last Sync:
                                        <b>
                                            ${escHtml(i.last_sync_label)}
                                        </b>
                                    </span>

                                    <span>
                                        <b>
                                            ${i.object_count.toLocaleString()}
                                        </b>

                                        ${
                                            escHtml(
                                                d.metric||
                                                'objects'
                                            )
                                        }
                                    </span>

                                    <span
                                        class="
                                            jt-connector-errors
                                            ${
                                                err
                                                    ? 'bad'
                                                    : 'ok'
                                            }
                                        "
                                    >
                                        ${
                                            err
                                                ? `${err} errors / warnings`
                                                : '0 errors'
                                        }
                                    </span>

                                    ${
                                        d.note
                                            ? `
                                                <span>
                                                    ${escHtml(d.note)}
                                                </span>
                                            `
                                            : ''
                                    }

                                </div>
                            </div>
                        `;
                    }
                )
                .join('')
            }

        </div>
    `;

    stage.appendChild(box);

    box.querySelectorAll(
        '.jt-connector-card'
    ).forEach(
        el=>{
            el.onclick=()=>{
                const integration=
                    ints.find(
                        x=>
                            x.key===
                            el.dataset.key
                    );

                openConnector(
                    el.dataset.key,
                    integration
                );
            };
        }
    );
}

function openConnector(key,i){
    const d=
        i.details||{};

    const inactive=
        i.status!=='connected';

    modal(`
        <h3>
            ${escHtml(i.name)}
        </h3>

        ${tinyBadge(i.status)}

        <div class="jt-detail-grid">

            <div>
                <span>Last sync</span>
                <strong>
                    ${escHtml(i.last_sync_label)}
                </strong>
            </div>

            <div>
                <span>Objects</span>
                <strong>
                    ${i.object_count.toLocaleString()}
                </strong>
            </div>

            <div>
                <span>Errors</span>
                <strong>
                    ${d.errors||0}
                </strong>
            </div>

            <div>
                <span>Type</span>
                <strong>
                    ${escHtml(i.kind)}
                </strong>
            </div>

        </div>

        <p>
            ${
                escHtml(
                    d.note||
                    'Connector is operating under the finalist adapter contract.'
                )
            }
        </p>

        <div class="jt-modal-actions">

            <button
                class="jt-btn-ghost"
                onclick="closeJTModal()"
            >
                Close
            </button>

            ${
                inactive

                ? `
                    <button
                        class="jt-btn-primary"
                        id="connConnect"
                    >
                        Connect
                    </button>
                `

                : `
                    <button
                        class="jt-btn-ghost"
                        id="connPause"
                    >
                        Pause
                    </button>

                    <button
                        class="jt-btn-primary"
                        id="connSync"
                    >
                        Sync Now
                    </button>
                `
            }

        </div>
    `);

    if(inactive){
        document.getElementById(
            'connConnect'
        ).onclick=async()=>{
            try{
                await api(
                    `/integrations/${key}/connect`,
                    {
                        method:'POST',
                        body:JSON.stringify({
                            config:{
                                configured_in_finals:true
                            }
                        })
                    }
                );

                closeModal();

                toast(
                    `${i.name} connected and configuration persisted.`,
                    'ok'
                );

                adminHydrate();

            }catch(e){
                toast(
                    e.message,
                    'error'
                );
            }
        };

        return;
    }

    document.getElementById(
        'connPause'
    ).onclick=async()=>{
        try{
            await api(
                `/integrations/${key}/pause`,
                {
                    method:'POST'
                }
            );

            closeModal();

            toast(
                `${i.name} paused. State and ledger updated.`,
                'ok'
            );

            adminHydrate();

        }catch(e){
            toast(
                e.message,
                'error'
            );
        }
    };

    document.getElementById(
        'connSync'
    ).onclick=async()=>{
        try{
            const x=
                await api(
                    `/integrations/${key}/sync`,
                    {
                        method:'POST'
                    }
                );

            closeModal();

            toast(
                `${i.name}: +${x.details?.last_batch||0} objects; ${x.object_count.toLocaleString()} total.`,
                'ok'
            );

            adminHydrate();

        }catch(e){
            toast(
                e.message,
                'error'
            );
        }
    };
}

async function sync(k,n){
    try{
        const d=
            await api(
                `/integrations/${k}/sync`,
                {
                    method:'POST'
                }
            );

        toast(
            `${n} synchronized. ${d.object_count.toLocaleString()} objects now indexed.`,
            'ok'
        );

        if(JT.screen===9){
            adminHydrate();
        }

    }catch(e){
        toast(
            `${n}: ${e.message}`,
            'error'
        );
    }
}

function applyAdminState(cfg){
    cfg.rbac.forEach(
        p=>{
            const display=
                Object.keys(
                    ROLE_MAP
                ).find(
                    k=>
                        ROLE_MAP[k]===
                        p.role
                );

            if(display){
                visualCard(
                    display,
                    300,
                    55
                )?.classList.toggle(
                    'jt-policy-disabled',
                    !p.enabled
                );
            }
        }
    );

    cfg.shields.forEach(
        s=>{
            const display=
                Object.keys(
                    SHIELD_MAP
                ).find(
                    k=>
                        SHIELD_MAP[k]===
                        s.key
                );

            if(display){
                visualCard(
                    display,
                    300,
                    55
                )?.classList.toggle(
                    'jt-shield-disabled',
                    !s.enabled
                );
            }
        }
    );
}

/* ============================================================
   DRAGGABLE CONFLICT NETWORK
============================================================ */

function findGraphCanvas(){
    const c=
        leaf(
            'Central Core Rule'
        );

    if(!c)return null;

    let p=
        c.parentElement;

    while(
        p&&
        p!==stage
    ){
        const st=
            p.getAttribute(
                'style'
            )||'';

        if(
            st.includes(
                'height:700px'
            )&&
            st.includes(
                'position:relative'
            )
        ){
            return p;
        }

        p=p.parentElement;
    }

    return null;
}

function graphNodeEl(
    label,
    graph
){
    const e=
        leaf(label);

    if(!e)return null;

    let p=e;

    while(
        p&&
        p!==graph
    ){
        const st=
            (
                p.getAttribute(
                    'style'
                )||
                ''
            )
            .replace(/\s/g,'')
            .toLowerCase();

        if(
            st.includes(
                'position:absolute'
            )&&
            st.includes(
                'background:#12243a'
            )
        ){
            return p;
        }

        p=p.parentElement;
    }

    return null;
}

function initEvidenceGraph(){
    const graph=
        findGraphCanvas();

    if(!graph)return;

    graph.classList.add(
        'jt-graph-canvas'
    );

    /* Hide broken prototype connectors */

    [
        ...graph.querySelectorAll('div')
    ].forEach(
        el=>{
            const st=
                (
                    el.getAttribute(
                        'style'
                    )||
                    ''
                )
                .replace(/\s/g,'')
                .toLowerCase();

            if(
                st.includes(
                    'position:absolute'
                )&&
                (
                    st.includes(
                        'transform:rotate'
                    )||
                    st.includes(
                        'border-top:'
                    )
                )&&
                !el.innerText.trim()
            ){
                el.style.display='none';
            }
        }
    );

    const specs={
        central:
            'Central Core Rule',

        outlook:
            'Outlook Approval',

        teams:
            'Teams Message',

        fsd:
            'FSD v3.0 (Outdated)',

        complaint:
            'Customer Complaint',

        core:
            'Customer Core System'
    };

    const nodes={};

    Object.entries(specs)
        .forEach(
            ([id,label])=>{
                const n=
                    graphNodeEl(
                        label,
                        graph
                    );

                if(n){
                    nodes[id]=n;

                    n.dataset.graphNode=id;

                    n.classList.add(
                        'jt-network-node',
                        'jt-draggable-node',
                        'jt-clickable'
                    );

                    n.style.zIndex='5';
                }
            }
        );

    const svg=
        document.createElementNS(
            'http://www.w3.org/2000/svg',
            'svg'
        );

    svg.classList.add(
        'jt-graph-svg'
    );

    svg.innerHTML=`
        <defs>

            <filter id="edgeGlow">
                <feGaussianBlur
                    stdDeviation="2"
                    result="b"
                />

                <feMerge>
                    <feMergeNode in="b"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>

            <marker
                id="arrowCyan"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
            >
                <path
                    d="M 0 0 L 10 5 L 0 10 z"
                    fill="#20C7E8"
                />
            </marker>

        </defs>

        <circle
            class="jt-graph-halo"
            cx="50%"
            cy="50%"
            r="140"
        ></circle>
    `;

    graph.prepend(svg);

    const specsE=[
        [
            'central',
            'outlook',
            '#23C483',
            'approved',
            true
        ],

        [
            'central',
            'teams',
            '#F3A847',
            'informal',
            true
        ],

        [
            'central',
            'fsd',
            '#F05454',
            'conflict',
            true
        ],

        [
            'central',
            'complaint',
            '#20C7E8',
            'impact',
            true
        ],

        [
            'central',
            'core',
            '#64748B',
            'runtime',
            true
        ],

        [
            'outlook',
            'fsd',
            '#23C483',
            'supersedes',
            false
        ],

        [
            'teams',
            'core',
            '#F3A847',
            'drives',
            false
        ],

        [
            'fsd',
            'core',
            '#F05454',
            'legacy rule',
            false
        ],

        [
            'core',
            'complaint',
            '#20C7E8',
            'customer effect',
            false
        ],

        [
            'teams',
            'complaint',
            '#F3A847',
            'duplicate request',
            false
        ]
    ];

    const edges=
        specsE.map(
            (
                [
                    a,
                    b,
                    color,
                    label,
                    main
                ],
                idx
            )=>{
                const p=
                    document.createElementNS(
                        'http://www.w3.org/2000/svg',
                        'path'
                    );

                p.dataset.a=a;
                p.dataset.b=b;

                p.setAttribute(
                    'stroke',
                    color
                );

                p.setAttribute(
                    'stroke-width',
                    main
                        ? '2'
                        : '1.25'
                );

                p.setAttribute(
                    'fill',
                    'none'
                );

                if(main){
                    p.setAttribute(
                        'marker-end',
                        'url(#arrowCyan)'
                    );
                }

                p.classList.add(
                    main
                        ? 'jt-live-edge-main'
                        : 'jt-live-edge-secondary'
                );

                svg.appendChild(p);

                const t=
                    document.createElementNS(
                        'http://www.w3.org/2000/svg',
                        'text'
                    );

                t.textContent=label;

                t.classList.add(
                    'jt-edge-label'
                );

                svg.appendChild(t);

                return {
                    p,
                    t,
                    a,
                    b,
                    idx
                };
            }
        );

    const center=n=>({
        x:
            n.offsetLeft+
            n.offsetWidth/2,

        y:
            n.offsetTop+
            n.offsetHeight/2
    });

    const update=()=>{
        svg.setAttribute(
            'viewBox',
            `0 0 ${graph.clientWidth} ${graph.clientHeight}`
        );

        edges.forEach(
            e=>{
                const A=nodes[e.a];
                const B=nodes[e.b];

                if(!A||!B)return;

                const p=center(A);
                const q=center(B);

                const mx=
                    (p.x+q.x)/2;

                const my=
                    (p.y+q.y)/2;

                const dx=
                    q.x-p.x;

                const dy=
                    q.y-p.y;

                const curve=
                    (
                        e.idx%2
                            ? 1
                            : -1
                    )*
                    Math.min(
                        50,
                        Math.hypot(dx,dy)*.12
                    );

                const len=
                    Math.hypot(dx,dy)||
                    1;

                const nx=
                    -dy/len;

                const ny=
                    dx/len;

                const cx=
                    mx+
                    nx*curve;

                const cy=
                    my+
                    ny*curve;

                e.p.setAttribute(
                    'd',
                    `M ${p.x} ${p.y} Q ${cx} ${cy} ${q.x} ${q.y}`
                );

                e.t.setAttribute(
                    'x',
                    mx+
                    nx*curve*.45
                );

                e.t.setAttribute(
                    'y',
                    my+
                    ny*curve*.45-
                    4
                );
            }
        );
    };

    const initial={};

    Object.entries(nodes)
        .forEach(
            ([id,n])=>{
                initial[id]={
                    left:n.offsetLeft,
                    top:n.offsetTop
                };
            }
        );

    update();

    let drag=null;
    let moved=false;

    Object.entries(nodes)
        .forEach(
            ([id,n])=>{

                n.setAttribute(
                    'title',
                    'Drag node • click to inspect'
                );

                n.setAttribute(
                    'tabindex',
                    '0'
                );

                n.addEventListener(
                    'pointerdown',
                    e=>{
                        if(e.button!==0)return;

                        e.preventDefault();

                        const r=
                            graph.getBoundingClientRect();

                        const sx=
                            graph.clientWidth/
                            r.width;

                        const sy=
                            graph.clientHeight/
                            r.height;

                        drag={
                            n,

                            ox:
                                (
                                    e.clientX-
                                    r.left
                                )*
                                sx-
                                n.offsetLeft,

                            oy:
                                (
                                    e.clientY-
                                    r.top
                                )*
                                sy-
                                n.offsetTop,

                            startX:e.clientX,
                            startY:e.clientY
                        };

                        moved=false;

                        n.setPointerCapture?.(
                            e.pointerId
                        );

                        n.classList.add(
                            'jt-dragging'
                        );
                    }
                );

                n.addEventListener(
                    'pointermove',
                    e=>{
                        if(
                            !drag||
                            drag.n!==n
                        ){
                            return;
                        }

                        const r=
                            graph.getBoundingClientRect();

                        const sx=
                            graph.clientWidth/
                            r.width;

                        const sy=
                            graph.clientHeight/
                            r.height;

                        let x=
                            (
                                e.clientX-
                                r.left
                            )*
                            sx-
                            drag.ox;

                        let y=
                            (
                                e.clientY-
                                r.top
                            )*
                            sy-
                            drag.oy;

                        x=Math.max(
                            8,
                            Math.min(
                                graph.clientWidth-
                                n.offsetWidth-
                                8,
                                x
                            )
                        );

                        y=Math.max(
                            8,
                            Math.min(
                                graph.clientHeight-
                                n.offsetHeight-
                                8,
                                y
                            )
                        );

                        n.style.left=
                            `${x}px`;

                        n.style.top=
                            `${y}px`;

                        if(
                            Math.hypot(
                                e.clientX-drag.startX,
                                e.clientY-drag.startY
                            )>4
                        ){
                            moved=true;
                        }

                        update();
                    }
                );

                const end=()=>{
                    if(
                        !drag||
                        drag.n!==n
                    ){
                        return;
                    }

                    n.classList.remove(
                        'jt-dragging'
                    );

                    drag=null;

                    setTimeout(
                        ()=>{
                            moved=false;
                        },
                        0
                    );
                };

                n.addEventListener(
                    'pointerup',
                    end
                );

                n.addEventListener(
                    'pointercancel',
                    end
                );

                n.addEventListener(
                    'click',
                    e=>{
                        e.stopPropagation();

                        if(moved)return;

                        const data={
                            central:[
                                'Central Core Rule',
                                'Decision rule',
                                'Income-document eligibility',
                                'Canonical rule under evaluation'
                            ],

                            outlook:[
                                'Outlook Approval',
                                'Outlook',
                                'Statements accepted',
                                'Product Owner • approved source'
                            ],

                            teams:[
                                'Teams Message',
                                'Microsoft Teams',
                                'Request payslips anyway',
                                'Informal operations channel'
                            ],

                            fsd:[
                                'FSD v3.0 (Outdated)',
                                'Functional Specification',
                                '3 months payslips compulsory',
                                'Legacy requirement'
                            ],

                            complaint:[
                                'Customer Complaint',
                                'Customer feedback',
                                'Frustrated sentiment',
                                'Customer impact signal'
                            ],

                            core:[
                                'Customer Core System',
                                'Operational system',
                                'Income document missing — case stalled',
                                'Observed system behavior'
                            ]
                        }[id];

                        evidenceModal(
                            ...data
                        );
                    }
                );
            }
        );

    const tb=
        document.createElement('div');

    tb.className=
        'jt-graph-toolbar';

    tb.innerHTML=`
        <span>
            ↔ Drag nodes
        </span>

        <span>
            10 live relationships
        </span>

        <button type="button">
            Reset layout
        </button>
    `;

    tb.querySelector(
        'button'
    ).onclick=e=>{
        e.stopPropagation();

        Object.entries(initial)
            .forEach(
                ([id,p])=>{
                    nodes[id].style.left=
                        `${p.left}px`;

                    nodes[id].style.top=
                        `${p.top}px`;
                }
            );

        update();

        toast(
            'Network layout reset.',
            'ok'
        );
    };

    graph.appendChild(tb);

    if(
        typeof ResizeObserver!=='undefined'
    ){
        new ResizeObserver(
            update
        ).observe(graph);
    }
}

/* ============================================================
   GENERIC CLICKABLE CARDS
============================================================ */

function makeCardsExplorable(){
    [
        ...stage.querySelectorAll(
            'div'
        )
    ].forEach(
        card=>{
            const s=
                getComputedStyle(card);

            const r=
                card.getBoundingClientRect();

            const radius=
                parseFloat(
                    s.borderRadius
                )||0;

            if(
                radius<5||
                r.width<150||
                r.height<48||
                r.width>720||
                r.height>360
            ){
                return;
            }

            if(
                card.classList.contains(
                    'jt-clickable'
                )||
                card.classList.contains(
                    'jt-network-node'
                )
            ){
                return;
            }

            const txt=
                norm(
                    card.innerText
                );

            if(txt.length<3){
                return;
            }

            card.classList.add(
                'jt-explorable-card'
            );
        }
    );
}

/* ============================================================
   GLOBAL SEARCH
============================================================ */

function globalSearch(){
    modal(`
        <h3>
            Query JurisTwin
        </h3>

        <p>
            Search cases, evidence
            and decision records.
        </p>

        <label>
            Query
        </label>

        <input
            id="gq"
            value="bank statement"
        >

        <div class="jt-modal-actions">

            <button
                class="jt-btn-ghost"
                onclick="closeJTModal()"
            >
                Cancel
            </button>

            <button
                class="jt-btn-primary"
                id="grun"
            >
                Search
            </button>

        </div>
    `);

    document.getElementById(
        'grun'
    ).onclick=async()=>{
        try{
            const q=
                document.getElementById(
                    'gq'
                ).value;

            const r=
                await api(
                    '/search',
                    {
                        method:'POST',
                        body:JSON.stringify({
                            query:q,
                            limit:8
                        })
                    }
                );

            closeModal();

            toast(
                `${
                    Array.isArray(r)
                        ? r.length
                        : r.results?.length??0
                } governed search results returned.`,
                'ok'
            );

        }catch(e){
            toast(
                e.message,
                'error'
            );
        }
    };
}

/* ============================================================
   SCREEN WIRING
============================================================ */

function wire(){
    nav(
        'Command Center',
        1
    );

    nav(
        'Case Workspace',
        2
    );

    nav(
        'Conflict Intelligence',
        3
    );

    nav(
        'Digital Twin',
        4
    );

    nav(
        'Enterprise Memory',
        8
    );

    nav(
        'Decision Ledger',
        6
    );

    nav(
        'AI Bodyguard',
        7
    );

    bind(
        'Integrations',
        ()=>{
            JT.adminMode=
                'integrations';

            go(9);
        }
    );

    bind(
        'Administration',
        ()=>{
            JT.adminMode=
                'administration';

            go(9);
        }
    );

    bind(
        'Start Guided Demo',
        guided
    );

    bind(
        'Sign In to Security Core',
        login
    );

    bind(
        'Enter Finalist Demo Environment',
        login
    );

    bind(
        'Sign in with Enterprise SSO',
        ()=>{
            toast(
                'Finals build uses the governed local demo identity.'
            );
        }
    );

    bind(
        'Forgot password?',
        ()=>{
            toast(
                'Use the provided finalist credentials.'
            );
        }
    );

    bind(
        'Investigate Income-Document Conflict',
        ()=>go(2)
    );

    bind(
        'Open Conflict Network Graph',
        ()=>go(3)
    );

    bind(
        'Simulate Resolution Options',
        ()=>go(4)
    );

    bind(
        'Adjust Weights',
        weights
    );

    bind(
        'Compare Metrics',
        compareTwinMetrics
    );

    bind(
        'Submit Scenario for Approval',
        submitApproval
    );

    bind(
        'Approve & Publish Resolution',
        approve
    );

    bind(
        'Reject',
        rejectApproval
    );

    bind(
        'Request Changes',
        requestApprovalChanges
    );

    bind(
        'Compare Versions',
        compareVersions
    );

    bind(
        'Export Audit Report',
        exportLedger
    );

    bind(
        'Restore Approved Version (Recommend)',
        restore
    );

    bind(
        'Review Activity',
        reviewBodyguardActivity
    );

    bind(
        'Request Explanation',
        requestBodyguardExplanation
    );

    bind(
        'Escalate to Compliance',
        escalateBodyguard
    );

    bind(
        'Revoke User Access',
        revokeBodyguardAccess
    );

    bind(
        'Revoke Access',
        revokeBodyguardAccess
    );

    bind(
        'Mark as Authorised Overwrite',
        authorizeBodyguardOverwrite
    );

    bind(
        'Search customers, policies, decisions, messages or evidence…',
        memorySearch
    );

    bind(
        'Query decisions, logs or entities...',
        globalSearch
    );
}

function wireInteractiveExtras(){
    bind(
        'All systems operational',
        systemHealth
    );

    bind(
        'Michelle Tan',
        profileModal
    );

    bind(
        'JurisTwin',
        ()=>{
            if(JT.token){
                go(1);
            }
        }
    );

    bind(
        'JurisTwin Sentinel',
        ()=>{
            JT.token
                ? go(1)
                : go(0);
        }
    );

    if(JT.screen===1){
        bindCard(
            'Active Cases',
            async()=>{
                try{
                    const xs=
                        await api(
                            '/cases'
                        );

                    infoModal(
                        'Active Case Portfolio',
                        `
                            <p>
                                <strong>
                                    ${xs.length}
                                </strong>
                                governed customer
                                cases available.
                            </p>

                            <div class="jt-mini-list">
                                ${
                                    xs
                                    .slice(0,6)
                                    .map(
                                        x=>`
                                            <div>
                                                <b>
                                                    ${escHtml(x.case_ref)}
                                                </b>

                                                <span>
                                                    ${escHtml(x.customer_name)}
                                                    ·
                                                    ${escHtml(x.risk_status)}
                                                </span>
                                            </div>
                                        `
                                    )
                                    .join('')
                                }
                            </div>
                        `
                    );

                }catch(e){
                    toast(
                        e.message,
                        'error'
                    );
                }
            },
            180,
            80
        );

        bindCard(
            'Decision Conflicts',
            ()=>showConflictSummary(),
            180,
            80
        );

        bindCard(
            'Customers at Risk',
            showCaseSummary,
            180,
            80
        );

        bindCard(
            'Protected Decisions',
            showLedgerIntegrity,
            180,
            80
        );

        bindCard(
            'Security Alerts',
            ()=>go(7),
            180,
            80
        );
    }

    if(JT.screen===2){
        bind(
            'Aina Rahman',
            showCaseSummary
        );

        bind(
            'Primary Bank Statement',
            ()=>documentModal(
                'Primary Bank Statement',
                'Verified',
                'Three consecutive bank statements have been validated.'
            )
        );

        bind(
            'Income Affirmation PDF',
            ()=>documentModal(
                'Income Affirmation PDF',
                'Unresolved',
                'Eligibility is unresolved under the legacy rule.'
            )
        );

        bind(
            'Identity Proof (DL)',
            ()=>documentModal(
                'Identity Proof (DL)',
                'Verified',
                'Identity evidence passed validation.'
            )
        );

        bind(
            'FSD v3.0',
            ()=>evidenceModal(
                'FSD v3.0',
                'Functional Specification',
                'Payslips required under legacy rules.',
                'Legacy documentation'
            )
        );

        bind(
            'Outlook Approval',
            ()=>evidenceModal(
                'Outlook Approval',
                'Email',
                'Product Owner approved bank statements as an alternative.',
                'Product Owner'
            )
        );

        bind(
            'Teams Message',
            ()=>evidenceModal(
                'Teams Message',
                'Microsoft Teams',
                'Operations continued requesting payslips.',
                'Operations Officer'
            )
        );

        bind(
            'Customer Complaint',
            ()=>evidenceModal(
                'Customer Complaint',
                'Customer channel',
                "You keep asking for papers I don't have. Please resolve!",
                'Customer signal'
            )
        );
    }

    if(JT.screen===3){
        bind(
            'Root Cause',
            ()=>showConflictSummary()
        );

        bind(
            'Resolution Recommendation',
            ()=>showConflictSummary()
        );

        bind(
            'High Confidence',
            ()=>showConflictSummary()
        );
    }

    if(JT.screen===4){
        ['A','B','C'].forEach(
            x=>
                bindCard(
                    `OPTION ${x}`,
                    ()=>selectTwinOption(x),
                    310,
                    180
                )
        );

        selectTwinOption(
            JT.selectedOption||
            'C'
        );
    }

    if(JT.screen===5){
        bind(
            '27 Active Apps',
            showCaseSummary
        );

        bind(
            '5 Rejected Cases',
            ()=>{
                infoModal(
                    'Reconsideration Cohort',
                    '<p>Five previously rejected cases are flagged for fast-track review.</p>'
                );
            }
        );

        bind(
            '8 QA Tests',
            ()=>{
                infoModal(
                    'QA Impact',
                    '<p>Eight QA checks reference the outdated payslip-only rule.</p>'
                );
            }
        );

        bind(
            '3 ClickUp Tasks',
            ()=>{
                infoModal(
                    'Operational Tasks',
                    '<p>Three implementation tasks coordinate the process update.</p>'
                );
            }
        );
    }

    if(JT.screen===7){
        bindCard(
            'Protected decisions',
            showLedgerIntegrity,
            200,
            80
        );

        bindCard(
            'High-risk incidents',
            reviewBodyguardActivity,
            200,
            80
        );

        bind(
            'Why was this flagged?',
            requestBodyguardExplanation
        );
    }

    if(JT.screen===8){
        [
            'Source: All',
            'Customer: Any',
            'Project: Sentinel',
            'Decision Tiers',
            'Authority Level',
            'Sensitivity: Restricted',
            'Compliance Status',
            'v4.2 Active',
            'Date Range: 30D'
        ].forEach(
            t=>
                bind(
                    t,
                    ()=>toggleFilter(t)
                )
        );

        bindCard(
            'Manager View (Full Access)',
            ()=>switchMemoryRole('Manager'),
            280,
            140
        );

        bindCard(
            'Officer View (Assigned Cases Only)',
            ()=>switchMemoryRole('Officer'),
            280,
            140
        );

        bindCard(
            'Intern View (Redacted Tiers)',
            ()=>switchMemoryRole('Intern'),
            280,
            140
        );
    }

    if(JT.screen===9){
        [
            'Manager',
            'Officer',
            'Intern',
            'Compliance Auditor',
            'Product Owner',
            'QA Analyst'
        ].forEach(
            r=>
                bind(
                    r,
                    ()=>roleInfo(r)
                )
        );

        [
            'Data Sensitivity Masking',
            'Active DLP Protection',
            '7-Year Ledger Retention',
            'OOH Modification Guard'
        ].forEach(
            t=>
                bind(
                    t,
                    ()=>toggleShield(t)
                )
        );
    }
}

/* ============================================================
   PAGE HYDRATION
============================================================ */

async function hydrate(){
    try{
        if(JT.screen===1){
            await dashboard();
        }

        if(JT.screen===4){
            JT.sim=
                await api(
                    '/simulations/conflict/CF-INCOME-001'
                );

            updateTwinUI(
                JT.sim
            );
        }

        if(JT.screen===5){
            await approvalHydrate();
        }

        if(JT.screen===6){
            await ledgerHydrate();
        }

        if(JT.screen===7){
            await bodyguardHydrate();
        }

        if(JT.screen===8){
            await memoryHydrate();
        }

        if(JT.screen===9){
            await adminHydrate();
        }

    }catch(e){
        console.warn(
            'Hydration warning:',
            e
        );
    }
}

/* ============================================================
   KEYBOARD CONTROLS
============================================================ */

window.addEventListener(
    'keydown',
    async e=>{

        const tag=
            document.activeElement
                ?.tagName;

        const typing=
            tag==='INPUT'||
            tag==='TEXTAREA';

        if(e.key==='Escape'){
            closeModal();
        }

        if(
            (e.ctrlKey||e.metaKey)&&
            e.key.toLowerCase()==='k'
        ){
            e.preventDefault();

            JT.screen===8
                ? memorySearch()
                : globalSearch();

            return;
        }

        if(!typing){
            if(
                e.key==='+'||
                e.key==='='
            ){
                setZoom(
                    (JT.zoom||1)+.1
                );
            }

            if(e.key==='-'){
                setZoom(
                    (JT.zoom||1)-.1
                );
            }

            if(e.key==='0'){
                JT.zoom=1;
                fit();
            }

            if(
                !e.ctrlKey&&
                !e.metaKey&&
                e.key.toLowerCase()==='f'
            ){
                presentationToggle(
                    'focus'
                );
            }

            if(
                !e.ctrlKey&&
                !e.metaKey&&
                e.key.toLowerCase()==='c'
            ){
                presentationToggle(
                    'contrast'
                );
            }

            if(
                !e.ctrlKey&&
                !e.metaKey&&
                e.key.toLowerCase()==='m'
            ){
                presentationToggle(
                    'motion'
                );
            }
        }

        if(
            e.ctrlKey&&
            e.shiftKey&&
            e.key.toLowerCase()==='r'
        ){
            e.preventDefault();

            try{
                await api(
                    '/demo/reset',
                    {
                        method:'POST'
                    }
                );

                JT.sim=null;
                JT.approval=null;
                JT.alert=null;

                toast(
                    'Finals dataset reset.',
                    'ok'
                );

                render(1);

            }catch(x){
                toast(
                    x.message,
                    'error'
                );
            }
        }
    }
);

/* ============================================================
   SAFE JURISTWIN STARTUP
   IMPORTANT:
   NOTHING SHOULD START THE APP BEFORE THIS BLOCK.
============================================================ */

async function startJurisTwin(){
    try{
        /*
         * All constants including zoomLabel
         * have now been initialized.
         */
        fit();

        /*
         * Validate saved session if one exists.
         */
        if(JT.token){
            try{
                await api(
                    '/auth/me'
                );

                await render(1);

                return;

            }catch(e){
                console.warn(
                    'Saved JurisTwin session invalid:',
                    e
                );

                localStorage.removeItem(
                    'jt_token'
                );

                JT.token=null;
            }
        }

        /*
         * No valid session:
         * load System Access page.
         */
        await render(0);

    }catch(e){
        console.error(
            'JurisTwin startup failed:',
            e
        );

        stage.innerHTML=`
            <div
                style="
                    width:1440px;
                    height:1024px;
                    background:#07111F;
                    color:#F8FAFC;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-family:
                        Inter,
                        Segoe UI,
                        sans-serif
                "
            >
                <div
                    style="
                        max-width:720px;
                        padding:32px;
                        border:
                            1px solid #F05454;
                        background:#0D1B2A;
                        border-radius:12px
                    "
                >
                    <h2
                        style="
                            margin:0 0 12px;
                            color:#F05454
                        "
                    >
                        JurisTwin UI startup error
                    </h2>

                    <div
                        style="
                            font-size:16px;
                            line-height:1.6;
                            color:#B9C7D8
                        "
                    >
                        ${
                            escHtml(
                                e?.message||
                                String(e)
                            )
                        }
                    </div>

                    <div
                        style="
                            margin-top:16px;
                            color:#20C7E8
                        "
                    >
                        Press Ctrl + F5 after
                        replacing app.js.
                    </div>
                </div>
            </div>
        `;
    }
}

/*
 * Wait until finals.html DOM is fully available.
 */
if(
    document.readyState===
    'loading'
){
    document.addEventListener(
        'DOMContentLoaded',
        startJurisTwin,
        {
            once:true
        }
    );
}else{
    startJurisTwin();
}