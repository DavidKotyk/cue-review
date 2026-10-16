'use strict';
let doc = null, busy = false;
const $ = id => document.getElementById(id);
const labels = {reading_speed:'Reading speed',long_line:'Long line',too_many_lines:'More than 2 lines',short_duration:'Under 1 second',overlap:'Timing overlap'};
function el(tag, text, cls) {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function status(message,error=false){$('status').textContent=message;$('status').className=error?'error':'';}
function lock(value){busy=value;document.querySelectorAll('button,input,select,textarea').forEach(n=>n.disabled=value);}
async function api(path,data){const r=await fetch(path,data?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}:{});const v=await r.json();if(!r.ok)throw Error(v.error||'Local request failed.');return v;}
async function run(fn){if(busy)return;lock(true);try{await fn();}catch(e){status(e.message,true);}finally{lock(false);}}
function update(value){doc=value;localStorage.setItem('cue-review-id',doc.id);render();}
function details(m){const d=el('div');d.append(el('div',`${m.cps} chars/s · ${m.characters} characters · ${m.lines} line${m.lines===1?'':'s'}`,'caption-meta'));const badges=el('div',undefined,'issues');m.issues.forEach(x=>badges.append(el('span',labels[x]||x,'issue')));if(!m.issues.length)badges.append(el('span','Within this review profile','good'));d.append(badges);return d;}
function button(text,cls,fn){const b=el('button',text,cls);b.type='button';b.addEventListener('click',()=>run(fn));return b;}
function render(){
 $('review').hidden=false;$('filename').textContent=`${doc.name} · revision ${doc.revision}`;
 $('total').textContent=doc.cues.length;$('flagged').textContent=doc.cues.filter(c=>c.after.issues.length).length;$('approved').textContent=doc.cues.filter(c=>c.approved!==null).length;$('pending').textContent=doc.cues.filter(c=>c.proposal).length;
 const list=$('cues');list.replaceChildren();
 for(const c of doc.cues){
  if($('onlyFlagged').checked&&!c.after.issues.length)continue;
  const card=el('article',undefined,'cue');card.dataset.index=c.index;
  const head=el('div',undefined,'cue-head');head.append(el('span',`CUE ${String(c.index).padStart(3,'0')}`,'cue-num'),el('span',c.timing,'time'));card.append(head);
  const grid=el('div',undefined,'cue-grid'),left=el('div');left.append(el('div','SOURCE / UNCHANGED','caption-label'),el('p',c.original,'caption-text'),details(c.before));
  if(c.approved!==null){left.append(el('p','✓ Approved for export','approved-label'),el('p',c.approved,'caption-text'),details(c.after));}
  const right=el('div',undefined,'proposal');right.append(el('div','YOUR REVIEW','caption-label'));
  if(c.proposal){
   const edit=el('textarea');edit.value=c.proposal.text;edit.setAttribute('aria-label',`Edit suggestion for cue ${c.index}`);right.append(edit,el('p',`${c.proposal.model} · ${c.proposal.elapsed_seconds}s · check meaning before approval`,'model-meta'));
   const draftStats=el('p',undefined,'caption-meta');const estimate=()=>{const text=edit.value,lines=text.split('\n'),cps=text.replace(/\s+/g,' ').length/((c.end-c.start)/1000);draftStats.textContent=`Draft: ${cps.toFixed(2)} chars/s · ${lines.length} lines${cps>doc.profile.max_cps?' · still above speed target':''}${lines.some(l=>l.length>doc.profile.max_line)?' · long line remains':''}`;};edit.addEventListener('input',estimate);estimate();right.append(draftStats);
   const actions=el('div',undefined,'actions');actions.append(button('Approve this edit','',async()=>{update(await api('/api/decide',{id:doc.id,revision:doc.revision,index:c.index,action:'approve',text:edit.value}));status(`Cue ${c.index} approved. Only this text will replace the original on export.`);}),button('Reject','secondary',async()=>{update(await api('/api/decide',{id:doc.id,revision:doc.revision,index:c.index,action:'reject'}));status(`Suggestion rejected for cue ${c.index}.`);}));right.append(actions);
  }else{right.append(el('p',c.approved!==null?'This edit is approved. You can restore the original or request a fresh suggestion from it.':'A suggestion is a draft. Nothing changes until you approve it.','empty'));right.append(button('Suggest a tighter cut','secondary',async()=>{status(`Local phi3 is considering cue ${c.index}… this can take up to 90 seconds.`);update(await api('/api/propose',{id:doc.id,revision:doc.revision,index:c.index}));status(`Draft for cue ${c.index} is ready. Check meaning and remaining warnings.`);}));}
  if(c.approved!==null)right.append(button('Restore original','secondary',async()=>{update(await api('/api/decide',{id:doc.id,revision:doc.revision,index:c.index,action:'restore'}));status(`Original restored for cue ${c.index}.`);}));
  grid.append(left,right);card.append(grid);list.append(card);
 }
 if(!list.children.length)list.append(el('p','No cues match this filter.','empty'));
}
async function importText(source,name){const glossary=$('glossary').value.split(',').map(t=>t.trim()).filter(Boolean);update(await api('/api/import',{source,name,glossary,max_cps:Number($('cps').value)}));status('Review opened. Suggestions use local inference only when requested.');}
$('demo').addEventListener('click',()=>run(async()=>{const r=await fetch('/demo.srt');await importText(await r.text(),'studio-demo.srt');}));
$('file').addEventListener('change',()=>run(async()=>{const file=$('file').files[0];if(!file)return;if(file.size>250000)throw Error('Choose an SRT smaller than 250 KB.');await importText(await file.text(),file.name);}));
$('onlyFlagged').addEventListener('change',render);
$('reload').addEventListener('click',()=>run(async()=>{update(await api('/api/review?id='+encodeURIComponent(doc.id)));status('Latest saved revision loaded.');}));
function download(text,name,type){const url=URL.createObjectURL(new Blob([text],{type}));const a=el('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('export').addEventListener('click',()=>run(async()=>{const result=await api('/api/export',{id:doc.id,revision:doc.revision});const base=doc.name.replace(/\.srt$/i,'').replace(/[^a-zA-Z0-9_-]/g,'_')||'captions';download(result.srt,base+'-reviewed.srt','text/plain');download(JSON.stringify(result.audit,null,2),base+'-audit.json','application/json');status('SRT and audit exported. Your browser may ask to allow both downloads. Remaining timing/readability warnings are recorded in the audit.');}));
const saved=localStorage.getItem('cue-review-id');if(saved)run(async()=>{update(await api('/api/review?id='+encodeURIComponent(saved)));status('Your saved review is back.');});
