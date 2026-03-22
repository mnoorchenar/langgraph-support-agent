'use strict';
let sessionId = uuid4(), isStreaming = false, streamEl = null, streamBuf = '';
let toolChart = null, latChart = null;
const _pending = {};
const NODES = ['router','agent','tool_executor','responder'];
const TOOL_ICONS = {search_faq:'🔍',check_order_status:'📦',create_ticket:'🎫',get_product_info:'🛍️',escalate_to_human:'👤'};
const NODE_COLORS = {router:'#4f8ef7',agent:'#22c55e',tool_executor:'#f59e0b',responder:'#a78bfa'};

function uuid4(){return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;return(c==='x'?r:(r&0x3|0x8)).toString(16)})}
function esc(t){return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function fmt(v){return v>=1000?(v/1000).toFixed(1)+'k':v}
function dark(){return document.documentElement.getAttribute('data-theme')!=='light'}

document.addEventListener('DOMContentLoaded',()=>{
    document.getElementById('sessionBadge').textContent = sessionId.slice(0,8)+'…';
    updateBadge();
    initCharts();
});

function toggleTheme(){
    const n = dark()?'light':'dark';
    document.documentElement.setAttribute('data-theme',n);
    localStorage.setItem('lgsa-theme',n);
    rebuildCharts();
}
function updateBadge(){
    const v = document.getElementById('modelSelect').value;
    document.querySelectorAll('#mbadgeRow [data-mid]').forEach(el=>{el.style.display=el.dataset.mid===v?'inline-flex':'none'});
}
function fill(t){const el=document.getElementById('msgInput');el.value=t;el.focus();autoResize(el)}
function autoResize(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px'}
function onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}

function newChat(){
    if(isStreaming)return;
    sessionId=uuid4();
    document.getElementById('sessionBadge').textContent=sessionId.slice(0,8)+'…';
    document.getElementById('messages').innerHTML=`<div class="welcome" id="welcomeScreen"><div class="welcome-icon">🤖</div><div class="welcome-title">TechStore Support Agent</div><p class="welcome-sub">Start a new conversation.</p><div class="welcome-chips"><div class="wchip" onclick="fill(this.textContent)">What is your return policy?</div><div class="wchip" onclick="fill(this.textContent)">Track order ORD-482910</div><div class="wchip" onclick="fill(this.textContent)">Do you have laptops in stock?</div></div></div>`;
    document.getElementById('toolLog').innerHTML='<div class="empty-state"><div class="empty-icon">🛠️</div>Tool calls will appear here</div>';
    document.getElementById('traceLog').innerHTML='<div class="empty-state"><div class="empty-icon">🗺️</div>Send a message to start tracing</div>';
    document.getElementById('histLog').innerHTML='<div class="empty-state"><div class="empty-icon">📜</div>Conversation history will appear here</div>';
    NODES.forEach(n=>setNode(n,'pending',null));
    setStatus('ready');
    ['sbTurns','sbTools','sbTok','stTurns','stTools','stTok'].forEach(id=>{const el=document.getElementById(id);if(el)el.textContent='0'});
    ['sbLat','stLat'].forEach(id=>{const el=document.getElementById(id);if(el)el.textContent='—'});
    if(toolChart){toolChart.data.labels=[];toolChart.data.datasets[0].data=[];toolChart.update()}
    if(latChart){latChart.data.labels=[];latChart.data.datasets[0].data=[];latChart.update()}
    fetch('/api/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,model:document.getElementById('modelSelect').value})});
}

async function send(){
    if(isStreaming)return;
    const input=document.getElementById('msgInput');
    const msg=input.value.trim();
    if(!msg)return;
    const welcome=document.getElementById('welcomeScreen');
    if(welcome)welcome.remove();
    input.value='';input.style.height='auto';
    isStreaming=true;streamBuf='';
    document.getElementById('sendBtn').disabled=true;
    setStatus('thinking');
    NODES.forEach(n=>setNode(n,'pending',null));
    appendMsg('user',msg);
    streamEl=appendMsg('assistant','',true);
    try{
        const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg,model:document.getElementById('modelSelect').value,session_id:sessionId})});
        const reader=res.body.getReader();const dec=new TextDecoder();let buf='';
        while(true){
            const{done,value}=await reader.read();
            if(done)break;
            buf+=dec.decode(value,{stream:true});
            const parts=buf.split('\n\n');buf=parts.pop();
            for(const p of parts){if(p.startsWith('data: ')){try{handleEv(JSON.parse(p.slice(6)))}catch(e){console.warn(e)}}}
        }
    }catch(err){showErr('Connection error: '+err.message);finalize(null)}
}

function handleEv(ev){
    switch(ev.type){
        case 'token': addToken(ev.content);break;
        case 'node_enter': setNode(ev.node,'running',null);break;
        case 'node_exit': setNode(ev.node,'completed',ev.duration_ms);addTrace(ev.node,ev.duration_ms);break;
        case 'tool_call': addTool(ev);break;
        case 'tool_result': updateTool(ev);break;
        case 'done': finalize(ev.message.content);updateStats(ev.analytics);addHist(ev.message);break;
        case 'error': showErr(ev.message);finalize(null);break;
    }
}

function addToken(t){
    streamBuf+=t;
    if(!streamEl)return;
    const b=streamEl.querySelector('.msg-bubble');
    if(!b)return;
    const cur=b.querySelector('.cursor');
    if(cur)cur.insertAdjacentText('beforebegin',t);
}

function finalize(content){
    isStreaming=false;
    document.getElementById('sendBtn').disabled=false;
    setStatus('ready');
    if(streamEl){
        const b=streamEl.querySelector('.msg-bubble');
        const cur=b?b.querySelector('.cursor'):null;
        if(cur)cur.remove();
        if(content&&b)b.textContent=content;
        streamEl.classList.remove('msg-streaming');
        streamEl=null;
    }
    streamBuf='';
    scrollChat();
}

function appendMsg(role,content,streaming=false){
    const c=document.getElementById('messages');
    const d=document.createElement('div');
    d.className=`msg ${role}${streaming?' msg-streaming':''}`;
    const av=role==='user'?'👤':'🤖';
    const bub=streaming?`<div class="msg-bubble">${esc(content)}<span class="cursor"></span></div>`:`<div class="msg-bubble">${esc(content)}</div>`;
    d.innerHTML=`<div class="msg-av">${av}</div><div>${bub}<div class="msg-meta">${role}</div></div>`;
    c.appendChild(d);scrollChat();return d;
}
function scrollChat(){const c=document.getElementById('messages');c.scrollTop=c.scrollHeight}

function setNode(node,state,ms){
    const el=document.getElementById('gn-'+node);if(!el)return;
    el.className='gn '+state;
    const d=document.getElementById('gd-'+node);
    if(d)d.textContent=ms!=null?ms+'ms':(state==='running'?'…':'—');
}

function addTrace(node,ms){
    const tl=document.getElementById('traceLog');
    const emp=tl.querySelector('.empty-state');if(emp)emp.remove();
    const color=NODE_COLORS[node]||'#8892a4';
    const d=document.createElement('div');d.className='trace-entry';
    d.innerHTML=`<div class="trace-dot" style="background:${color}"></div><div class="trace-name">${node}</div><div class="trace-dur">${ms!=null?ms+'ms':'—'}</div>`;
    tl.insertBefore(d,tl.firstChild);
    if(tl.children.length>20)tl.lastChild.remove();
}

function addTool(ev){
    const log=document.getElementById('toolLog');
    const emp=log.querySelector('.empty-state');if(emp)emp.remove();
    const icon=TOOL_ICONS[ev.name]||'🔧';
    const id='te-'+Date.now();
    const d=document.createElement('div');d.className='tool-entry';d.id=id;
    d.innerHTML=`<div class="tool-header" onclick="toggleTool('${id}')"><div class="tool-icon">${icon}</div><div class="tool-name">${ev.name}</div><div class="tool-lat" id="${id}-lat">…</div><div class="tool-chevron"><i class="fas fa-chevron-right"></i></div></div><div class="tool-body"><div class="tool-slabel">Input</div><div class="tool-pre">${esc(JSON.stringify(ev.input,null,2))}</div><div class="tool-slabel">Output</div><div class="tool-pre" id="${id}-out">Waiting…</div></div>`;
    log.insertBefore(d,log.firstChild);
    _pending[ev.name]=id;
}

function updateTool(ev){
    const id=_pending[ev.name];if(!id)return;
    const out=document.getElementById(id+'-out');if(out)out.textContent=ev.output;
    const lat=document.getElementById(id+'-lat');if(lat)lat.textContent=(ev.latency_ms||0)+'ms';
    delete _pending[ev.name];
}
function toggleTool(id){document.getElementById(id).classList.toggle('open')}

function updateStats(d){
    if(!d)return;
    document.getElementById('sbTurns').textContent=d.turn_count;
    document.getElementById('sbTools').textContent=d.tool_call_count;
    document.getElementById('sbTok').textContent=fmt(d.total_tokens);
    document.getElementById('sbLat').textContent=d.avg_latency_ms?d.avg_latency_ms+'ms':'—';
    document.getElementById('stTurns').textContent=d.turn_count;
    document.getElementById('stTools').textContent=d.tool_call_count;
    document.getElementById('stTok').textContent=fmt(d.total_tokens);
    document.getElementById('stLat').textContent=d.avg_latency_ms?d.avg_latency_ms+'ms':'—';
    if(toolChart&&d.tool_usage){toolChart.data.labels=Object.keys(d.tool_usage);toolChart.data.datasets[0].data=Object.values(d.tool_usage);toolChart.update('none')}
    if(latChart&&d.latency_history){latChart.data.labels=d.latency_history.map((_,i)=>'T'+(i+1));latChart.data.datasets[0].data=d.latency_history;latChart.update('none')}
}

function addHist(msg){
    const log=document.getElementById('histLog');
    const emp=log.querySelector('.empty-state');if(emp)emp.remove();
    const ts=msg.timestamp?new Date(msg.timestamp).toLocaleTimeString():'';
    const d=document.createElement('div');d.className='hist-entry';
    d.innerHTML=`<div class="hist-role ${msg.role}">${msg.role}</div><div class="hist-content">${esc(msg.content.slice(0,280))}${msg.content.length>280?'…':''}</div><div class="hist-meta"><span>${ts}</span>${msg.token_count?'<span>~'+msg.token_count+' tokens</span>':''}</div>`;
    log.insertBefore(d,log.firstChild);
}

function setStatus(s){
    const dot=document.getElementById('sdot');const txt=document.getElementById('stext');
    dot.className='sdot'+(s==='thinking'?' thinking':s==='error'?' error':'');
    txt.textContent={ready:'Ready',thinking:'Thinking…',error:'Error'}[s]||s;
}

function switchTab(name,btn){
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-'+name).classList.add('active');
    if(name==='stats')rebuildCharts();
}

function chartColors(){
    const d=dark();
    return{text:d?'#8892a4':'#4b5675',grid:d?'rgba(255,255,255,.05)':'rgba(0,0,0,.07)',
        tip:{backgroundColor:d?'rgba(7,13,31,.97)':'rgba(255,255,255,.97)',titleColor:d?'#e2e8f0':'#0f172a',bodyColor:d?'#8892a4':'#4b5675',borderColor:d?'rgba(79,142,247,.3)':'rgba(37,99,235,.2)',borderWidth:1}};
}

function initCharts(){
    const c=chartColors();
    const base={responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:c.tip}};
    const sc={ticks:{color:c.text},grid:{color:c.grid}};
    toolChart=new Chart(document.getElementById('toolChart'),{type:'bar',data:{labels:[],datasets:[{data:[],backgroundColor:['rgba(79,142,247,.7)','rgba(245,158,11,.7)','rgba(34,197,94,.7)','rgba(6,182,212,.7)','rgba(167,139,250,.7)'],borderRadius:4}]},options:{...base,indexAxis:'y',scales:{x:sc,y:sc}}});
    latChart=new Chart(document.getElementById('latChart'),{type:'line',data:{labels:[],datasets:[{data:[],borderColor:'#4f8ef7',backgroundColor:'rgba(79,142,247,.08)',borderWidth:2,pointRadius:3,tension:.4,fill:true}]},options:{...base,scales:{x:sc,y:{...sc,title:{display:true,text:'ms',color:c.text,font:{size:10}}}}}});
}

function rebuildCharts(){if(toolChart){toolChart.destroy();toolChart=null}if(latChart){latChart.destroy();latChart=null}initCharts()}

function showErr(msg){
    setStatus('error');
    const t=document.createElement('div');t.className='err-toast';t.textContent='⚠ '+msg;
    document.body.appendChild(t);setTimeout(()=>t.remove(),5000);
}